from flask import Flask, render_template, request
import math
import locale

app = Flask(__name__)

# Configurar locale para pt_BR
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
    return render_template("index.html")


@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    resultado = None
    pv = fv = pmt = i = n = entrada = 0.0
    calc_what = "pv"
    tem_entrada = False

    if request.method == "POST":
        calc_what = request.form.get('calc_what', 'pv')
        pv = to_float_zero(request.form.get('pv', ''))
        fv = to_float_zero(request.form.get('fv', ''))
        pmt = to_float_zero(request.form.get('pmt', ''))
        i = to_float_zero(request.form.get('i', '')) / 100
        n = to_float_zero(request.form.get('n', ''))
        entrada = to_float_zero(request.form.get('entrada', ''))
        tem_entrada = 'tem_entrada' in request.form

        try:
            if calc_what == "pv":
                if i != 0:
                    resultado_valor = (
                        fv - pmt * ((1 + i) ** n - 1) / i) / ((1 + i) ** n)
                else:
                    resultado_valor = fv - pmt * n
                resultado = f"Valor Presente (PV): R$ {format_brl(resultado_valor)}"

            elif calc_what == "fv":
                base = pv + entrada if tem_entrada else pv
                if i != 0:
                    resultado_valor = base * \
                        ((1 + i) ** n) + pmt * (((1 + i) ** n - 1) / i)
                else:
                    resultado_valor = base + pmt * n
                resultado = f"Valor Futuro (FV): R$ {format_brl(resultado_valor)}"

            elif calc_what == "pmt":
                base = pv + entrada if tem_entrada else pv
                if i == 0:
                    resultado_valor = (fv - base) / n if n != 0 else 0.0
                else:
                    resultado_valor = (
                        fv - base * ((1 + i) ** n)) * i / (((1 + i) ** n) - 1)
                resultado = f"Pagamento (PMT): R$ {format_brl(resultado_valor)}"

            elif calc_what == "n":
                base = pv + entrada if tem_entrada else pv
                A = base * i + pmt
                B = fv * i + pmt
                if A == 0 or B <= 0 or i <= 0:
                    resultado = "Não foi possível calcular n com os valores fornecidos."
                else:
                    n_val = math.log(B / A) / math.log(1 + i)
                    resultado = f"Períodos (n): {format_brl(n_val, 4)}"

            elif calc_what == "i":
                base = pv + entrada if tem_entrada else pv
                guess = 0.01
                for _ in range(10000):
                    try:
                        if guess == 0:
                            fvi = base + pmt * n
                        else:
                            fvi = base * ((1 + guess) ** n) + \
                                pmt * (((1 + guess) ** n - 1) / guess)
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

        except Exception as e:
            resultado = f"Erro no cálculo: {str(e)}"

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
                           entrada=to_str_or_blank(entrada),
                           tem_entrada=tem_entrada,
                           calc_what=calc_what)


if __name__ == "__main__":
    app.run(debug=True)
