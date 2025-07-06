from flask import Flask, render_template, request
import math
import locale

app = Flask(__name__)

# Configurar locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Se no Windows ou sistema não reconhecer pt_BR.UTF-8, tentar outro padrão
    locale.setlocale(locale.LC_ALL, '')


@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    pv = fv = pmt = i = n = 0.0
    calc_what = "pv"  # padrão

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
            # fallback simples
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if request.method == "POST":
        calc_what = request.form.get('calc_what', 'pv')

        pv = to_float_zero(request.form.get('pv', ''))
        fv = to_float_zero(request.form.get('fv', ''))
        pmt = to_float_zero(request.form.get('pmt', ''))
        i = to_float_zero(request.form.get('i', '')) / \
            100  # converte para decimal
        n = to_float_zero(request.form.get('n', ''))

        if i is None:
            i = 0.0

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
                    resultado_valor = pv * \
                        ((1 + i) ** n) + pmt * (((1 + i) ** n - 1) / i)
                else:
                    resultado_valor = pv + pmt * n
                resultado = f"Valor Futuro (FV): R$ {format_brl(resultado_valor)}"

            elif calc_what == "pmt":
                if i == 0:
                    resultado_valor = (fv - pv) / n if n != 0 else 0.0
                else:
                    resultado_valor = (fv - pv * ((1 + i) ** n)
                                       ) * i / (((1 + i) ** n) - 1)
                resultado = f"Pagamento (PMT): R$ {format_brl(resultado_valor)}"

            elif calc_what == "n":
                A = pv * i + pmt
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
                            fvi = pv + pmt * n
                        else:
                            fvi = pv * ((1 + guess) ** n) + pmt * \
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

        except Exception as e:
            resultado = f"Erro no cálculo: {str(e)}"

    def to_str_or_blank(v):
        if v is None or v == 0:
            return ""
        if isinstance(v, float):
            # Formatar para string no padrão brasileiro
            return format_brl(v, 4 if calc_what in ['i', 'n'] else 2)
        return str(v)

    return render_template("index.html",
                           resultado=resultado,
                           pv=to_str_or_blank(pv),
                           fv=to_str_or_blank(fv),
                           pmt=to_str_or_blank(pmt),
                           i=to_str_or_blank(i * 100),
                           n=to_str_or_blank(n),
                           calc_what=calc_what)


if __name__ == "__main__":
    app.run(debug=True)
