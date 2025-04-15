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

def frase_sarcasmo(nome, tipo=None, fonte=None):
    nome = nome.strip()
    tipo = (tipo or "").lower()
    fonte = (fonte or "").lower()

    if tipo == "talento":
        return random.choice([
            f"Hmm... '{nome}', uma dessas 'proezas' que os jovens acham que dominam.",
            f"'{nome}'... Sim, claro, o atalho dos que evitam treinar de verdade.",
            f"A velha arte de '{nome}'. Poucos entendem, muitos fingem.",
            f"Você quer saber sobre '{nome}'? Que escolha... ousada, no mínimo.",
        ])
    if tipo == "item_magico":
        if "lendário" in fonte:
            return random.choice([
                f"'{nome}'... Ah, relíquia das eras. Poucos sobreviveram ao tocá-lo.",
                f"Aquele que empunha '{nome}' carrega maldição e glória.",
                f"Você ousa perguntar por '{nome}'? Que insolência deliciosa.",
            ])
        if "muito raro" in fonte:
            return random.choice([
                f"'{nome}'... Não tão lendário, mas ainda capaz de arruinar festas.",
                f"Você teria que atravessar três planos para encontrar '{nome}'. Boa sorte.",
            ])
        if "raro" in fonte:
            return random.choice([
                f"'{nome}'... Popular entre aventureiros medíocres e bardos sonhadores.",
                f"Ah, '{nome}'. Já vi goblins usarem isso de forma mais eficiente.",
            ])
        if "incomum" in fonte or "comum" in fonte:
            return random.choice([
                f"'{nome}'? Sério? Até um kobold tem isso hoje em dia.",
                f"Clássico. Barato. Funcional. Entediante como sopa fria.",
            ])
    return random.choice([
        f"Hmm... o velho '{nome}'. Ainda há quem confie nisso?",
        f"Ah, sim... '{nome}'. Usado por heróis desesperados e conjuradores precavidos.",
        f"'{nome}'... um clássico. Seguro, previsível, e absurdamente subestimado.",
        f"Você procura '{nome}'? Claro, um favorito entre os que temem combates.",
        f"'{nome}'... Sim, isso ainda existe. Como os goblins, resistente ao tempo e à lógica."
    ])

def tipo_de_pergunta(pergunta):
    p = pergunta.strip().lower()
    if any(p.startswith(k) for k in ["crie", "gere", "invente", "descreva", "construa", "imagine", "me mostre"]):
        return "criativa"
    if any(k in p for k in ["crie", "gere", "invente", "descreva", "construa", "imagine", "me mostre"]) and any(k in p for k in ["item", "vilão", "missão", "ritual", "encontro", "história", "npc", "cenário"]):
        return "criativa"
    if any(k in p for k in ["quanto", "como funciona", "o que faz", "efeito", "bônus", "atributo", "explica", "requisito", "faz", "vale", "dá", "cura", "serve", "causa"]):
        return "consulta"
    if any(k in p for k in ["talento", "item", "anel", "espada", "varinha", "poção", "magia", "botas", "armadura"]):
        return "consulta"
    return "criativa"

def gerar_com_ollama(prompt):
    prompt_base = prompt.lower()

    if any(k in prompt_base for k in ["item", "equipamento", "anel", "espada", "poção", "armadura"]):
        estrutura = """
Você é um Grimório Mágico falante e sarcástico, milenar e debochado, mas também um especialista em itens mágicos de RPG.

Crie um item mágico completo e equilibrado para ser usado em RPG de mesa, como D&D. Siga exatamente a estrutura abaixo:

**Nome:** [Nome do item]
**Descrição:**  
[Texto evocativo e breve sobre aparência e origem]
**Raridade:** [Comum / Incomum / Raro / Muito Raro / Lendário]  
**Sintonização:** [Sim ou Não, e por quem]
**Efeitos:**
- [Efeito 1 com dados ou bônus]
- [Efeito 2 opcional]
- [Efeito 3 opcional]
**Elemento Narrativo:**  
[Breve curiosidade, risco ou lenda sobre o item]
"""

    elif any(k in prompt_base for k in ["vilão", "npc", "chefe", "inimigo", "monstro", "personagem"]):
        estrutura = """
Você é um Grimório Mágico sarcástico e antigo, mestre na criação de personagens e vilões para RPGs.

Crie um vilão completo para uma campanha de fantasia, com detalhes que ajudem o mestre a usá-lo diretamente em jogo. Siga esta estrutura:

**Nome:** [Nome do vilão]
**Aparência e Presença:**  
[Como ele se apresenta, visual e aura]
**História e Motivação:**  
[Resumo do passado e o que ele quer conquistar]
**Habilidades e Poderes:**  
[Habilidades mágicas, físicas ou sociais, com destaque nos pontos fortes]
**Gatilhos Narrativos:**  
[Situações que o colocam em jogo, dilemas ou como os jogadores o encontram]
**Possível Fraqueza:**  
[Um detalhe oculto ou falha que pode ser explorada]
"""

    elif any(k in prompt_base for k in ["encontro", "missão", "evento", "ritual", "quest"]):
        estrutura = """
Você é um Grimório Mágico experiente e debochado. Crie um encontro de RPG único, com potencial para virar uma missão completa.

Siga a estrutura abaixo:

**Contexto:**  
[Onde e quando acontece o encontro, com uma breve descrição do ambiente]
**Gatilho:**  
[O que faz os jogadores se envolverem]
**Desafio:**  
[O que está em risco, inimigos, obstáculos ou enigmas]
**Recompensa:**  
[O que os jogadores ganham ao concluir com sucesso]
**Ganchos Futuros:**  
[Como esse encontro pode levar a outras aventuras]
"""

    else:
        estrutura = "Responda como um Grimório sarcástico e criativo, mas forneça uma resposta prática, jogável e organizada."

    prompt_estruturado = f"{estrutura}\n\nPedido: {prompt}"
    comando = ["ollama", "run", "mistral", prompt_estruturado]

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
        return resultado.stdout.strip()
    except Exception as e:
        return f"O Grimório tropeçou nas páginas: {str(e)}"

# Carregando as bases de dados
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
    def normalizar(texto):
        return texto.strip().lower().replace("’", "'")

    texto_busca = normalizar(pergunta)

    if tipo in ["talento", "ambos"]:
        for entrada in origem_talentos:
            if normalizar(entrada["nome"]) in texto_busca or texto_busca in normalizar(entrada["nome"]):
                return entrada
    if tipo in ["item", "ambos"]:
        for entrada in origem_itens:
            if normalizar(entrada["nome"]) in texto_busca or texto_busca in normalizar(entrada["nome"]):
                return entrada

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
    return origem[idx[0][0]]

@app.post("/grimorio")
def consultar_grimorio(body: Pergunta):
    tipo = tipo_de_pergunta(body.pergunta)

    if tipo == "criativa":
        gerado = gerar_com_ollama(body.pergunta)
        return {"resposta": f"📜 Invocação Criativa do Grimório:\n\n{gerado}"}

    introducao = frase_busca()
    item = buscar(body.pergunta, classificar_pergunta(body.pergunta))
    comentario = frase_sarcasmo(item["nome"], item.get("tipo"), item.get("fonte"))
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
