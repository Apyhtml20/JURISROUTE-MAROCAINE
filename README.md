# 🚔 JURISROUTE MAROCAIN 
### Plateforme intelligente d'assistance juridique routière basée sur l'IA

<p align="center">
  <img width="505" height="93" alt="JurisRoute Logo" src="./frontend/public/logos/jurisroute-hero.svg" />
</p>

---

## 📌 Descriptioncc

**JURISROUTE MAROCAIN** est une plateforme web intelligente dédiée à la **gestion du Code de la Route marocain**, à la **consultation juridique automatisée**, et à la **génération intelligente de procès-verbaux routiers** assistée par Intelligence Artificielle.

Ce projet vise à moderniser l'accès à l'information juridique routière au Maroc grâce à :

- 🤖 Chatbot IA spécialisé dans le droit routier marocain  
- 📄 Génération automatique de PV routiers  
- 📚 Recherche intelligente dans les lois et sanctions  
- 🧠 Système RAG (Retrieval-Augmented Generation)   
- 👤 Gestion utilisateurs complète avec PHP

---

## 🖼️ Aperçu

<p align="center">
  <img alt="JurisRoute - Code de la Route" src="./assets/Capture d'écran 2026-06-12 234234.png" />
</p>

---

## 🧠 Intelligence Artificielle utilisée

Le projet repose sur un modèle **fine-tuné personnellement** pour le domaine juridique marocain.

### 🔹 Base Model :

**Qwen2-0.5B-Instruct**

### 🔹 Méthode de Fine-Tuning :

- LoRA (Low Rank Adaptation)
- Entraînement supervisé sur dataset spécialisé
- Optimisé pour réponses juridiques rapides
- Déploiement local possible via Ollama / Transformers

### 🔹 Modèle disponible sur Hugging Face :

👉 https://huggingface.co/ApyHTML19/JurisRoute-qwen2-LoRa

---

## 🤗 Dataset personnalisé

Dataset entièrement **collecté, structuré et nettoyé manuellement** par moi-même.

### Contenu :

- Code de la route marocain  
- Infractions routières  
- Sanctions officielles  
- Questions / Réponses juridiques  
- Cas pratiques  
- Procès-verbaux routiers  

### Disponible sur Hugging Face :

👉 https://huggingface.co/datasets/ApyHTML19/JurisRoute_CODE_MAROCAIN

---

## ⚙️ Stack Technique

| Partie | Technologie |
|--------|-------------|
| Frontend | Laravel + Blade + JavaScript |
| Backend | FastAPI et Python |
| IA Locale | Ollama |
| LLM | Qwen2 Fine-Tuned LoRA  |
| Vector DB | Faiss |
| OCR | Python OCR |
| Base de données | MySQL |
| Conteneurisation | Docker |

---

## 🧱 Architecture

```text
Frontend Laravel
      ↓
API FastAPI
      ↓
RAG Engine + FAISS
      ↓
Qwen2 LoRA Fine-Tuned
      ↓
Réponse intelligente
```
