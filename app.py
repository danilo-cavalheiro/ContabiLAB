from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    if request.method == 'POST':
        try:
            pv = float(request.form['pv'])
            i = float(request.form['i']) / 100  # porcentagem
            n = int(request.form['n'])
            resultado = pv * ((1 + i) ** n)
        except:
            resultado = "Erro no cálculo. Verifique os valores."

    return render_template('index.html', resultado=resultado)


if __name__ == '__main__':
    app.run(debug=True)
