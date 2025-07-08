from flask import Flask, render_template, request
import math
import locale
import requests

app = Flask(__name__)

# Disponibilizar 'request' para os templates


@app.context_processor
def inject_request():
    return dict(request=request)


# Configurar locale pt_BR
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')


def to_float_zero(s):
    s = s.replace(',', '.') if s else ''
    try:
        return float(s) if s else 0.0
    except:
        return 0.0


def format_brl(value, decimals=2):
    try:
        return locale.format_string(f"%.{decimals}f", value, grouping=True)
    except:
        return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@app.route("/")
def home():
    # Aqui é a página inicial, mostrar botão hamburguer
    return render_template("index.html", is_tool=False)


@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    resultado = None
    pv = fv = pmt = i = n = entrada = 0.0
    calc_what = "pv"
    tem_entrada = False
    tabela = None

    if request.method == "POST":
        calc_what = request.form.get('calc_what', 'pv')
        tem_entrada = request.form.get('tem_entrada') == 'on'
        entrada = to_float_zero(request.form.get('entrada', ''))
        pv = to_float_zero(request.form.get('pv', ''))
        fv = to_float_zero(request.form.get('fv', ''))
        pmt = to_float_zero(request.form.get('pmt', ''))
        i = to_float_zero(request.form.get('i', '')) / 100
        n = to_float_zero(request.form.get('n', ''))

        pv_ajustado = pv - entrada if tem_entrada else pv

        try:
            if calc_what == "pv":
                if i != 0:
                    resultado_valor = (
                        fv - pmt * ((1 + i) ** n - 1) / i) / ((1 + i) ** n)
                else:
                    resultado_valor = fv - pmt * n
                resultado = f"Valor Presente (PV): R$ {format_brl(resultado_valor)}"

            elif calc_what == "fv":
                if i != 0:
                    resultado_valor = pv_ajustado * \
                        ((1 + i) ** n) + pmt * (((1 + i) ** n - 1) / i) + \
                        entrada * ((1 + i) ** n)
                else:
                    resultado_valor = pv_ajustado + pmt * n + entrada
                resultado = f"Valor Futuro (FV): R$ {format_brl(resultado_valor)}"

            elif calc_what == "pmt":
                if i == 0:
                    resultado_valor = (fv - pv_ajustado) / n if n != 0 else 0.0
                else:
                    resultado_valor = (
                        fv - pv_ajustado * ((1 + i) ** n)) * i / (((1 + i) ** n) - 1)
                resultado = f"Pagamento (PMT): R$ {format_brl(resultado_valor)}"

            elif calc_what == "n":
                A = pv_ajustado * i + pmt
                B = fv * i + pmt
                if A == 0 or B <= 0 or i <= 0:
                    resultado = "Não foi possível calcular n com os valores fornecidos."
                else:
                    n_val = math.log(B / A) / math.log(1 + i)
                    resultado = f"Períodos (n): {format_brl(n_val, 4)}"

            elif calc_what == "i":
                guess = 0.01
                for _ in range(10000):
                    try:
                        if guess == 0:
                            fvi = pv_ajustado + pmt * n
                        else:
                            fvi = pv_ajustado * \
                                ((1 + guess) ** n) + pmt * \
                                (((1 + guess) ** n - 1) / guess)
                        diff = fv - fvi
                        if abs(diff) < 0.0001:
                            break
                        guess += diff / 1000000
                    except ZeroDivisionError:
                        guess += 0.0001
                resultado_valor = guess * 100
                resultado = f"Taxa de Juros (i): {format_brl(resultado_valor, 4)} % ao período"

            else:
                resultado = "Escolha um cálculo válido."

            if calc_what in ["fv", "i", "pmt"] and n > 0 and (pmt != 0 or calc_what == "fv"):
                saldo = pv_ajustado
                taxa = i
                tabela = []
                for periodo in range(1, int(n) + 1):
                    juros = saldo * taxa
                    amort = (pmt - juros) if pmt != 0 else 0
                    saldo -= amort
                    tabela.append({
                        'n': periodo,
                        'pv': format_brl(saldo if saldo > 0 else 0),
                        'juros': format_brl(juros),
                        'amort': format_brl(amort),
                        'pmt': format_brl(pmt)
                    })
            else:
                tabela = None

        except Exception as e:
            resultado = f"Erro no cálculo: {str(e)}"
            tabela = None

    def to_str_or_blank(v):
        if v is None or v == 0:
            return ""
        if isinstance(v, float):
            return format_brl(v, 4 if calc_what in ['i', 'n'] else 2)
        return str(v)

    return render_template("calculadora.html",
                           resultado=resultado,
                           pv=to_str_or_blank(pv),
                           fv=to_str_or_blank(fv),
                           pmt=to_str_or_blank(pmt),
                           i=to_str_or_blank(i * 100),
                           n=to_str_or_blank(n),
                           calc_what=calc_what,
                           tem_entrada=tem_entrada,
                           entrada=to_str_or_blank(entrada),
                           tabela=tabela,
                           is_tool=True)  # <-- Aqui!


@app.route("/depreciacao", methods=["GET", "POST"])
def depreciacao():
    resultado = None
    valor_aquisicao = valor_residual = vida_util = consumo = 0.0

    if request.method == "POST":
        valor_aquisicao = to_float_zero(
            request.form.get('valor_aquisicao', ''))
        valor_residual = to_float_zero(request.form.get('valor_residual', ''))
        vida_util = to_float_zero(request.form.get('vida_util', ''))
        consumo = to_float_zero(request.form.get('consumo', ''))

        try:
            valor_depreciavel = valor_aquisicao - valor_residual

            if vida_util == 0:
                raise ValueError("Vida útil não pode ser zero.")

            # cálculo correto da depreciação do período
            valor_depreciacao = valor_depreciavel * (consumo / vida_util)

            resultado = {
                'valor_aquisicao': format_brl(valor_aquisicao),
                'valor_residual': format_brl(valor_residual),
                'valor_depreciavel': format_brl(valor_depreciavel),
                'vida_util': f"{vida_util:.2f}",
                'consumo': f"{consumo:.4f}",
                'valor_depreciacao': format_brl(valor_depreciacao)
            }

        except Exception as e:
            resultado = {'erro': f"Erro no cálculo: {str(e)}"}

    return render_template("depreciacao.html",
                           resultado=resultado,
                           valor_aquisicao=request.form.get(
                               'valor_aquisicao', ''),
                           valor_residual=request.form.get(
                               'valor_residual', ''),
                           vida_util=request.form.get('vida_util', ''),
                           consumo=request.form.get('consumo', ''),
                           is_tool=True)  # <-- Aqui!


@app.route("/cambio", methods=["GET", "POST"])
def cambio():
    resultado = None
    valor = None
    moeda_origem = None
    moeda_destino = None
    erro = None

    if request.method == "POST":
        try:
            valor = float(request.form.get("valor", "0").replace(',', '.'))
            moeda_origem = request.form.get("moeda_origem", "USD").upper()
            moeda_destino = request.form.get("moeda_destino", "BRL").upper()

            # Sua chave da API ExchangeRate-API
            API_KEY = "64172d2728696ea20bdb861c"
            url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{moeda_origem}"

            response = requests.get(url)
            data = response.json()

            if data["result"] == "success":
                taxas = data["conversion_rates"]
                if moeda_destino in taxas:
                    taxa = taxas[moeda_destino]
                    valor_convertido = valor * taxa
                    resultado = f"{valor:.2f} {moeda_origem} = {valor_convertido:.2f} {moeda_destino}"
                else:
                    erro = f"Moeda destino '{moeda_destino}' não suportada."
            else:
                erro = "Erro ao consultar a API de câmbio."

        except Exception as e:
            erro = f"Erro: {str(e)}"

    moedas = ["USD", "BRL", "EUR", "GBP", "JPY",
              "AUD", "CAD", "CHF", "CNY", "INR"]

    return render_template("cambio.html",
                           resultado=resultado,
                           valor=valor if valor is not None else "",
                           moeda_origem=moeda_origem if moeda_origem else "USD",
                           moeda_destino=moeda_destino if moeda_destino else "BRL",
                           erro=erro,
                           moedas=moedas,
                           is_tool=True)  # <-- Aqui!


if __name__ == "__main__":
    app.run(debug=True)
