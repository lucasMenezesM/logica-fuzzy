# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# === Definição do sistema fuzzy ===
# Variáveis linguísticas (universos)
pressao_sistolica = ctrl.Antecedent(
    np.arange(80, 201, 1), 'pressao_sistolica')    # mmHg
pressao_diastolica = ctrl.Antecedent(
    np.arange(50, 131, 1), 'pressao_diastolica')  # mmHg
idade = ctrl.Antecedent(np.arange(0, 101, 1),
                        'idade')                             # anos

# 0..100 representa o score de risco
risco = ctrl.Consequent(np.arange(0, 101, 1), 'risco')

# === Funções de pertinência ===
# Pressão Sistólica
pressao_sistolica['baixa'] = fuzz.trapmf(
    pressao_sistolica.universe, [80, 80, 90, 110])
pressao_sistolica['normal'] = fuzz.trimf(
    pressao_sistolica.universe, [100, 120, 130])
pressao_sistolica['alta'] = fuzz.trimf(
    pressao_sistolica.universe, [125, 145, 160])
pressao_sistolica['muito_alta'] = fuzz.trapmf(
    pressao_sistolica.universe, [155, 170, 200, 200])

# Pressão Diastólica
pressao_diastolica['baixa'] = fuzz.trapmf(
    pressao_diastolica.universe, [50, 50, 55, 70])
pressao_diastolica['normal'] = fuzz.trimf(
    pressao_diastolica.universe, [60, 75, 85])
pressao_diastolica['alta'] = fuzz.trimf(
    pressao_diastolica.universe, [80, 90, 100])
pressao_diastolica['muito_alta'] = fuzz.trapmf(
    pressao_diastolica.universe, [95, 105, 130, 130])

# Idade
idade['jovem'] = fuzz.trapmf(idade.universe, [0, 0, 18, 30])
idade['adulto'] = fuzz.trimf(idade.universe, [25, 40, 60])
idade['idoso'] = fuzz.trapmf(idade.universe, [55, 65, 100, 100])

# Saída - Risco
risco['baixo'] = fuzz.trapmf(risco.universe, [0, 0, 10, 30])
risco['moderado'] = fuzz.trimf(risco.universe, [20, 40, 60])
risco['alto'] = fuzz.trimf(risco.universe, [50, 70, 85])
risco['critico'] = fuzz.trapmf(risco.universe, [80, 90, 100, 100])

# === Regras do sistema fuzzy ===
regras = []

# Pressão sistólica ou diastólica muito alta -> risco crítico
regras.append(ctrl.Rule(pressao_sistolica['muito_alta'] |
                        pressao_diastolica['muito_alta'], risco['critico']))

# Pressão sistólica alta e diastólica alta -> risco alto
regras.append(ctrl.Rule(
    pressao_sistolica['alta'] & pressao_diastolica['alta'], risco['alto']))

# Pressão sistólica alta, diastólica normal e pessoa idosa -> risco alto
regras.append(ctrl.Rule(
    pressao_sistolica['alta'] & pressao_diastolica['normal'] & idade['idoso'], risco['alto']))

# Pressão sistólica normal + diastólica normal -> risco baixo
regras.append(ctrl.Rule(
    pressao_sistolica['normal'] & pressao_diastolica['normal'], risco['baixo']))

# Pressão levemente alta em adulto -> risco moderado
regras.append(ctrl.Rule(
    (pressao_sistolica['alta'] & ~pressao_diastolica['muito_alta']) & idade['adulto'], risco['moderado']))
regras.append(ctrl.Rule(
    (pressao_diastolica['alta'] & ~pressao_sistolica['muito_alta']) & idade['adulto'], risco['moderado']))

# Pressão sistólica baixa, mas diastólica alta -> risco depende da idade
regras.append(ctrl.Rule(
    pressao_sistolica['baixa'] & pressao_diastolica['alta'] & idade['idoso'], risco['alto']))
regras.append(ctrl.Rule(
    pressao_sistolica['baixa'] & pressao_diastolica['alta'] & ~idade['idoso'], risco['moderado']))

# Idoso com pressão normal -> risco moderado (maior vulnerabilidade)
regras.append(ctrl.Rule(idade['idoso'] & pressao_sistolica['normal']
              & pressao_diastolica['normal'], risco['moderado']))

# Construção do sistema de controle
sistema_risco = ctrl.ControlSystem(regras)
simulador_risco = ctrl.ControlSystemSimulation(sistema_risco)

# === Função auxiliar para transformar valor em rótulo textual ===


def obter_label_risco(valor):
    if valor >= 80:
        return "CRÍTICO"
    if valor >= 60:
        return "ALTO"
    if valor >= 35:
        return "MODERADO"
    return "BAIXO"


# === Configuração da API Flask ===
app = Flask(__name__)
CORS(app)  # Permite chamadas do Next.js local; em produção configurar origens específicas


@app.route('/')
def index():
    return "API Fuzzy de Hipertensão - use /prever (POST JSON)."


@app.route('/predict', methods=['POST'])
def prever():
    """
    Corpo da requisição esperado:
    {
      "pressao_sistolica": 135,
      "pressao_diastolica": 85,
      "idade": 52
    }
    """
    dados = request.get_json(force=True)

    # Validação dos campos recebidos
    try:
        s = float(dados.get('systolic', None))
        d = float(dados.get('diastolic', None))
        i = float(dados.get('age', None))
    except Exception:
        return jsonify({"erro": "Campos inválidos. Forneça pressao_sistolica, pressao_diastolica e idade como números."}), 400

    # Garantir que os valores estejam dentro do universo definido (clipping)
    s = np.clip(s, pressao_sistolica.universe.min(),
                pressao_sistolica.universe.max())
    d = np.clip(d, pressao_diastolica.universe.min(),
                pressao_diastolica.universe.max())
    i = np.clip(i, idade.universe.min(), idade.universe.max())

    # Cálculo do sistema fuzzy
    try:
        simulador_risco.input['pressao_sistolica'] = s
        simulador_risco.input['pressao_diastolica'] = d
        simulador_risco.input['idade'] = i
        simulador_risco.compute()
        valor = float(simulador_risco.output['risco'])
        label = obter_label_risco(valor)
    except Exception as e:
        return jsonify({"erro": "Erro ao calcular o sistema fuzzy.", "detalhes": str(e)}), 500

    # Sugestões baseadas no risco identificado
    sugestoes = {
        "BAIXO": "Sem indicação imediata. Monitorar regularmente e manter estilo de vida saudável.",
        "MODERADO": "Consulte seu médico para avaliação. Monitorar pressão e hábitos.",
        "ALTO": "Procure orientação médica. Alterações no estilo de vida e possível tratamento.",
        "CRÍTICO": "Procure atendimento médico com urgência ou emergência."
    }

    return jsonify({
        "entrada": {"pressao_sistolica": s, "pressao_diastolica": d, "idade": i},
        "valor_risco": round(valor, 2),
        "label": label,
        "sugestao": sugestoes[label]
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
