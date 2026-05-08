# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from model import obeter_dados_e_treinar, prever_gravidade, get_stats

app = FastAPI(title="Triagem Respiratória IA - Backend")

# Permitir acesso do React (Front end em outra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientFeatures(BaseModel):
    idade: int
    saturacao: bool
    febre: bool
    tosse: bool
    garganta: bool
    dispneia: bool
    asma: bool
    diabetes: bool
    cardiopatia: bool

@app.post("/train")
async def train_model():
    """Lê os dados do banco Supabase e treina a Inteligência Artificial"""
    try:
        accuracy, samples = obeter_dados_e_treinar()
        return {"status": "success", "accuracy": accuracy, "samples": samples}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/predict")
async def predict_severity(patient: PatientFeatures):
    """Prediz a gravidade recebendo os sintomas da interface em JSON"""
    try:
        # Mesma ordem da extração de features
        prob = prever_gravidade([
            1 if patient.febre else 0,
            1 if patient.tosse else 0,
            1 if patient.garganta else 0,
            1 if patient.dispneia else 0,
            1 if patient.asma else 0,
            1 if patient.diabetes else 0,
            1 if patient.cardiopatia else 0,
            1 if patient.saturacao else 0,
            patient.idade / 100.0
        ])
        return {"probabilidadeGravidade": prob}
    except Exception as e:
        raise HTTPException(500, f"Erro interno ou modelo sem treinamento: {str(e)}")

@app.get("/status")
def status():
    return get_stats()
