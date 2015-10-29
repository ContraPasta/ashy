from flask import Flask, render_template, session, request
from ash.generator import VerseGenerator, Predicate, Constraint

app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='devkey',
    USERNAME='admin',
    PASSWORD='default'
))
#app.config.from_envvar('ASH_APP_SETTINGS', silent=False)

vg = VerseGenerator('the quick brown fox jumped over the lazy dog')

@app.route('/')
def show_index():
    text = vg.build_sequence(4, [], [])
    return render_template('index.html')

@app.route('/add_text')
def add_text():
    '''
    Should be called when the "Add text" button is click. Gets the current
    contents of the text box and adds it to the VerseGenerator instance.
    '''
    return 'Not implemented'

@app.route('/generate', methods=['GET', 'POST'])
def generate_poem():
    '''
    This should be run when the "Generate poem" button is clicked.
    It should get the current Predicates and Constraints specified by
    the user, and call `VerseGenerator.build_sequence`.
    '''
    poem_data = request.get_json(force=True)
    print(poem_data)
    return 'poem posted'
