
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Caminho de entrada
with open("conhecimento_talentos.json", encoding="utf-8") as f:
    dados = json.load(f)

# Preparar pastas
os.makedirs("base_vetorial_talentos", exist_ok=True)

# Lista de textos e origem (nome, tipo, conteúdo, fonte)
textos = []
origens = []

for entrada in dados:
    texto = f"{entrada['nome']}\n{entrada['conteudo']}"
    textos.append(texto)
    origens.append({
        "nome": entrada["nome"],
        "tipo": entrada["tipo"],
        "fonte": entrada["fonte"],
        "conteudo": entrada["conteudo"]
    })

# Vetorização
vectorizer = TfidfVectorizer(stop_words=None)
X = vectorizer.fit_transform(textos)

# Modelo
modelo = NearestNeighbors(n_neighbors=1, metric="cosine").fit(X)

# Salvar arquivos
with open("base_vetorial_talentos/textos.json", "w", encoding="utf-8") as f:
    json.dump(textos, f, indent=2, ensure_ascii=False)
with open("base_vetorial_talentos/origem.json", "w", encoding="utf-8") as f:
    json.dump(origens, f, indent=2, ensure_ascii=False)
with open("base_vetorial_talentos/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
with open("base_vetorial_talentos/modelo.pkl", "wb") as f:
    pickle.dump(modelo, f)

print("✅ Base vetorial de talentos criada com sucesso!")
