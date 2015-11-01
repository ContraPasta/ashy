from flask import Flask, render_template, session, request
from ash.generator import VerseGenerator, Predicate, Constraint
from ash.phonology import Word

app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='devkey',
    USERNAME='admin',
    PASSWORD='default'
))
#app.config.from_envvar('ASH_APP_SETTINGS', silent=False)

vg = VerseGenerator('the quick brown fox jumped over the lazy dog')

def convert_json(data):
    '''
    Convert a JSON object sent from the UI to a set of predicates and
    constraints to be applied to poem generation.
    '''
    constraints = []
    for feature, indices in data.items():
        method = getattr(Word, feature)
        constraints.append(Constraint(method, indices))

    return constraints

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
    constraints = convert_json(poem_data)
    poem_text = vg.build_sequence(8, [], constraints)
    return ' '.join([str(w) for w in poem_text])
