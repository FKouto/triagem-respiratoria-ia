# pyrefly: ignore [missing-import]
import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.model import obter_dados_e_treinar, prever_gravidade, get_stats

app = FastAPI(title="Triagem Respiratória IA - Backend")

# Em produção, defina ALLOWED_ORIGINS no .env com o domínio real do frontend.
# Exemplo: ALLOWED_ORIGINS=https://meu-app.com
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chave simples para proteger o endpoint de treinamento.
# Defina TRAIN_SECRET no .env. Sem ela, o endpoint retorna 403.
TRAIN_SECRET = os.environ.get("TRAIN_SECRET", "")

# Limiares de classificação centralizados no backend
LIMIAR_GRAVE    = 60.0
LIMIAR_MODERADO = 30.0


class PatientFeatures(BaseModel):
    idade: int
    febre: bool
    tosse: bool
    garganta: bool
    dispneia: bool
    saturacao: bool
    asma: bool
    diabetes: bool
    cardiopatia: bool


def _classificar(prob: float) -> str:
    """Converte probabilidade em rótulo de gravidade."""
    if prob >= LIMIAR_GRAVE:
        return "grave"
    if prob >= LIMIAR_MODERADO:
        return "moderado"
    return "leve"


@app.post("/train")
def train_model(x_train_secret: str = Header(default="")):
    """
    Lê os dados do Supabase e treina a IA.
    Requer o header X-Train-Secret com o valor definido em TRAIN_SECRET.
    """
    if TRAIN_SECRET and x_train_secret != TRAIN_SECRET:
        raise HTTPException(403, "Acesso não autorizado ao endpoint de treinamento.")
    try:
        accuracy, samples = obter_dados_e_treinar()
        return {"status": "success", "accuracy": accuracy, "samples": samples}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/predict")
async def predict_severity(patient: PatientFeatures):
    """
    Prediz a gravidade recebendo os sintomas em JSON.

    Ordem das features (deve ser idêntica à de feature_keys em model.py):
      FEBRE, TOSSE, GARGANTA, DISPNEIA, ASMA, DIABETES, CARDIOPATI, SATURACAO, idade_norm
    """
    try:
        features = [
            1 if patient.febre        else 0,
            1 if patient.tosse        else 0,
            1 if patient.garganta     else 0,
            1 if patient.dispneia     else 0,
            1 if patient.asma         else 0,
            1 if patient.diabetes     else 0,
            1 if patient.cardiopatia  else 0,
            1 if patient.saturacao    else 0,
            patient.idade / 100.0,           # normalização consistente com o treino
        ]
        prob = prever_gravidade(features)
        classificacao = _classificar(prob)
        return {
            "probabilidadeGravidade": prob,
            "classificacao": classificacao,
            "limiares": {
                "grave": LIMIAR_GRAVE,
                "moderado": LIMIAR_MODERADO,
            },
        }
    except Exception as e:
        raise HTTPException(500, f"Erro interno ou modelo sem treinamento: {str(e)}")


@app.get("/status")
def status():
    return get_stats()