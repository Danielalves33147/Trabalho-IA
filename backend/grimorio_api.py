from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import pickle
import random
import subprocess
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Pergunta(BaseModel):
    pergunta: str

# Funções auxiliares
def cortar_apenas_primeiro(texto):
    padrao = r"\n[A-ZÂÊÁÉÍÓÚÇ\s]{4,}\n"
    partes = re.split(padrao, texto)
    return partes[0].strip() if partes else texto

def frase_busca():
    return random.choice([
        "Um momento... deixemos as runas revelarem.",
        "Hmm... deixe-me ver nos recantos empoeirados da minha memória.",
        "Ah, mais uma busca? Tudo bem, folheando minhas entranhas...",
        "Hmph... abrindo uma página que ninguém lê desde a Quarta Era.",
        "Espere. Sim, encontrei algo entre as teias do conhecimento."
    ])

def frase_sarcasmo(nome):
    return random.choice([
        f"Hmm... o velho '{nome}'. Ainda há quem confie nisso?",
        f"Ah, sim... '{nome}'. Usado por heróis desesperados e conjuradores precavidos.",
        f"'{nome}'... um clássico. Seguro, previsível, e absurdamente subestimado.",
        f"Você procura '{nome}'? Claro, um favorito entre os que temem combates.",
        f"'{nome}'... Sim, isso ainda existe. Como os goblins, resistente ao tempo e à lógica."
    ])

def tipo_de_pergunta(pergunta):
    consulta_keywords = [
        "quanto", "como funciona", "o que faz", "efeito", "bônus", "atributo",
        "explica", "requisito", "talento", "item", "anel", "espada", "varinha", "poção", "magia", "botas", "armadura"
    ]
    criativa_keywords = [
        "crie", "gere", "invente", "me mostre", "imagine", "criar", "descreva", "construa",
        "vilão", "missão", "ritual", "encontro", "história", "npc", "cenário"
    ]
    p = pergunta.lower()
    if any(k in p for k in criativa_keywords) and not any(k in p for k in consulta_keywords):
        return "criativa"
    return "consulta"

def gerar_com_ollama(prompt):
    prompt_estruturado = f'''
Você é um mestre de RPG experiente. Quando receber um pedido, você irá gerar uma estrutura narrativa completa e evocativa para uma campanha, com estilo interpretativo e criativo.
Pedido: {prompt}
Responda como um Grimório falante: sarcástico, milenar e um tanto debochado.
'''
    comando = ["ollama", "run", "mistral", prompt_estruturado]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
        return resultado.stdout.strip()
    except Exception as e:
        return f"O Grimório tropeçou nas páginas: {str(e)}"

# Carregamento das bases
with open("conhecimento_talentos.json", encoding="utf-8") as f:
    talentos = json.load(f)
with open("base_vetorial_talentos/textos.json", encoding="utf-8") as f:
    textos_talentos = json.load(f)
with open("base_vetorial_talentos/origem.json", encoding="utf-8") as f:
    origem_talentos = json.load(f)
with open("base_vetorial_talentos/vectorizer.pkl", "rb") as f:
    vectorizer_tal = pickle.load(f)
with open("base_vetorial_talentos/modelo.pkl", "rb") as f:
    modelo_tal = pickle.load(f)

with open("conhecimento_itens_refinado.json", encoding="utf-8") as f:
    itens = json.load(f)
with open("base_vetorial_itens/textos.json", encoding="utf-8") as f:
    textos_itens = json.load(f)
with open("base_vetorial_itens/origem.json", encoding="utf-8") as f:
    origem_itens = json.load(f)
with open("base_vetorial_itens/vectorizer.pkl", "rb") as f:
    vectorizer_itm = pickle.load(f)
with open("base_vetorial_itens/modelo.pkl", "rb") as f:
    modelo_itm = pickle.load(f)

def classificar_pergunta(pergunta):
    texto = pergunta.lower()
    if any(t in texto for t in ["talento", "proeza", "habilidade"]):
        return "talento"
    if any(t in texto for t in ["item", "anel", "varinha", "espada", "manto", "equipamento", "poção"]):
        return "item"
    return "ambos"

def buscar(pergunta, tipo):
    if tipo == "talento":
        vec, mod, origem = vectorizer_tal, modelo_tal, origem_talentos
    elif tipo == "item":
        vec, mod, origem = vectorizer_itm, modelo_itm, origem_itens
    else:
        r1 = buscar(pergunta, "talento")
        r2 = buscar(pergunta, "item")
        return r1 if len(r1["conteudo"]) > len(r2["conteudo"]) else r2

    vetor = vec.transform([pergunta])
    _, idx = mod.kneighbors(vetor, n_neighbors=1)
    item = origem[idx[0][0]]
    return item

@app.post("/grimorio")
def consultar_grimorio(body: Pergunta):
    tipo = tipo_de_pergunta(body.pergunta)

    if tipo == "criativa":
        gerado = gerar_com_ollama(body.pergunta)
        return {"resposta": f"📜 Invocação Criativa do Grimório:\n\n{gerado}"}

    introducao = frase_busca()
    item = buscar(body.pergunta, classificar_pergunta(body.pergunta))
    comentario = frase_sarcasmo(item["nome"])
    resposta = (
        f"{introducao}\n\n"
        f"Grimório responde, com um suspiro imaginário...\n"
        f"{comentario}\n\n"
        f"📘 Nome: {item['nome']}\n"
        f"🔹 Tipo: {item['tipo']}\n"
        f"📗 Fonte: {item['fonte']}\n"
        f"🧾 Conteúdo:\n{cortar_apenas_primeiro(item['conteudo'])}"
    )
    return {"resposta": resposta}
