
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

with open("conhecimento_itens_refinado.json", encoding="utf-8") as f:
    dados = json.load(f)

os.makedirs("base_vetorial_itens", exist_ok=True)

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

vectorizer = TfidfVectorizer(stop_words=None)
X = vectorizer.fit_transform(textos)

modelo = NearestNeighbors(n_neighbors=1, metric="cosine").fit(X)

with open("base_vetorial_itens/textos.json", "w", encoding="utf-8") as f:
    json.dump(textos, f, indent=2, ensure_ascii=False)
with open("base_vetorial_itens/origem.json", "w", encoding="utf-8") as f:
    json.dump(origens, f, indent=2, ensure_ascii=False)
with open("base_vetorial_itens/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
with open("base_vetorial_itens/modelo.pkl", "wb") as f:
    pickle.dump(modelo, f)

print("✅ Base vetorial de itens criada com sucesso!")
