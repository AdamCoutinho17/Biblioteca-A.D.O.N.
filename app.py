from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ===== Inicialização do banco =====
def init_db():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()

    # Cria tabela de livros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            quantidade INTEGER DEFAULT 1
        )
    ''')

    # Cria tabela de empréstimos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL,
            id_livro INTEGER,
            FOREIGN KEY(id_livro) REFERENCES livros(id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ===== Página inicial =====
@app.route('/')
def index():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, titulo, autor, quantidade FROM livros')
    livros = cursor.fetchall()
    conn.close()
    return render_template('index.html', livros=livros)

# ===== Cadastro de livros =====
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        quantidade = int(request.form['quantidade'])
        conn = sqlite3.connect('biblioteca.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO livros (titulo, autor, quantidade) VALUES (?, ?, ?)', (titulo, autor, quantidade))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('cadastro.html')

# ===== Empréstimos =====
@app.route('/emprestimo', methods=['GET', 'POST'])
def emprestimo():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome_usuario = request.form['nome']
        id_livro = int(request.form['id_livro'])

        cursor.execute('SELECT quantidade, titulo FROM livros WHERE id = ?', (id_livro,))
        resultado = cursor.fetchone()
        if resultado:
            quantidade, titulo = resultado
            if quantidade > 0:
                nova_qtd = quantidade - 1
                cursor.execute('UPDATE livros SET quantidade = ? WHERE id = ?', (nova_qtd, id_livro))
                cursor.execute('INSERT INTO emprestimos (nome_usuario, id_livro) VALUES (?, ?)', (nome_usuario, id_livro))
                conn.commit()
                conn.close()
                return redirect('/')
            else:
                conn.close()
                # Livro indisponível → mostra tela de erro
                return render_template('erro.html', mensagem=f'O livro "{titulo}" está indisponível para empréstimo no momento.')
        else:
            conn.close()
            return render_template('erro.html', mensagem='Livro não encontrado.')

    cursor.execute('SELECT id, titulo, autor FROM livros')
    livros = cursor.fetchall()
    conn.close()
    return render_template('emprestimos.html', livros=livros)

# ===== Devolver livros =====
@app.route('/devolver', methods=['GET', 'POST'])
def devolver():
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        id_livro = int(request.form['id_livro'])

        # Atualiza quantidade do livro
        cursor.execute('SELECT quantidade FROM livros WHERE id = ?', (id_livro,))
        resultado = cursor.fetchone()
        if resultado:
            quantidade = resultado[0]
            nova_qtd = quantidade + 1
            cursor.execute('UPDATE livros SET quantidade = ? WHERE id = ?', (nova_qtd, id_livro))

        # Remove apenas o primeiro empréstimo do livro (sem LIMIT)
        cursor.execute('SELECT id FROM emprestimos WHERE id_livro = ? ORDER BY id ASC', (id_livro,))
        emprestimo = cursor.fetchone()
        if emprestimo:
            cursor.execute('DELETE FROM emprestimos WHERE id = ?', (emprestimo[0],))

        conn.commit()
        conn.close()
        return redirect('/')

    cursor.execute('''
        SELECT e.id_livro, l.titulo, l.autor, e.nome_usuario
        FROM emprestimos e
        JOIN livros l ON e.id_livro = l.id
    ''')
    emprestados = cursor.fetchall()
    conn.close()
    return render_template('devolver.html', emprestados=emprestados)

# ===== Excluir livros =====
@app.route('/excluir/<int:id_livro>')
def excluir(id_livro):
    conn = sqlite3.connect('biblioteca.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM livros WHERE id = ?', (id_livro,))
    cursor.execute('DELETE FROM emprestimos WHERE id_livro = ?', (id_livro,))
    conn.commit()
    cursor.execute('VACUUM')
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)