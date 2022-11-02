#!python3
# imports   ===================================================================
# standard
import os
import pathlib
import ast
from subprocess import check_output
from tempfile import NamedTemporaryFile

# external
from flask import (
    Flask,
    request,
    url_for,
    jsonify,
    redirect,
    make_response,
    render_template,
)
from werkzeug.exceptions import NotFound, HTTPException, InternalServerError


# APLICATION    ===============================================================
ALLOWED_EXTENTIONS  = ['csv']
ALLOWED_FILETYPES   = ['text/csv']


def allowed_file(fname, c_type):
    return '.' in fname and \
            ((fname.rsplit('.', -1)[1].lower() in ALLOWED_EXTENTIONS) or \
                (c_type in ALLOWED_FILETYPES))


def start_test(d='', m='', c=''):
    '''
    -d|--data-file DATA_FILE    - Dataset file name (default: None)
    -f|--features FEATURES      - features file name (default: None)
    -m|--metrics METRICS        - metrics modifier (default: None)
    -c|--classifier CLASSIFIER  - classifier modifier (default: None)
    -s|--silent                 - silent mode do not print options
                                (default: False)
    '''
    
    if not(d) or (d == ''): d = 0
    if not(m) or (m == ''): m = 0
    if not(c) or (c == ''): c = 0
    
    # always use `-s` for silent mode
    s = check_output('python3 %s -s -d %s -m %s -c %s' % (os.path.join(
        pathlib.Path(__file__).parents[1], 'Recommendation_system/test2.py'
    ), d, m, c), shell=True)
    return ast.literal_eval(str(s)).decode("UTF-8")


def check_opts(opt_key, r=False):
    s = check_output('python3 %s -l %s' % (os.path.join(
        pathlib.Path(__file__).parents[1], 'Recommendation_system/test2.py'
    ), opt_key), shell=True).decode("UTF-8").splitlines()
    if r: s = [os.path.basename(os.path.splitext(x)[0]) for x in s]
    return s if isinstance(s, list) else False


# app creator
def create_app():
    # application main warper
    app = Flask(__name__.split(':')[0])
    
    app.config['SECRET_KEY'] = "605248593ab5f926282281ee3848d0f0e87285a0"
    
    with app.app_context():
        @app.route('/upload', methods=['POST'])
        def upload_file():
            f = request.form
            m = f['metrics'] if 'metrics' in f else 0
            c = f['classifier'] if 'classifier' in f else 0

            if len(request.files) > 0 and request.files['the_file']:
                # check if a csv file
                fname = request.files['the_file'].filename
                c_type = request.files['the_file'].content_type
                if not allowed_file(fname, c_type):
                    return jsonify({'err': 'Filetype is not supported'})
                else:
                    # work with temp file
                    with NamedTemporaryFile() as f:
                        # f.write(request.files['the_file'].stream.read())
                        f.content_type = c_type
                        request.files['the_file'].save(f.name)
                        # ? ast.literal_eval
                        # just return string from script
                        return jsonify(start_test(f.name, m, c))

            return jsonify({'err': 'File is not provided!'})

        @app.route('/')
        def index():
            try:
                return render_template('index.html', options={
                    'metrics': check_opts('metrics'),
                    'classifier': check_opts('classifier')
                } )
            except: raise NotFound()
            
        @app.errorhandler(Exception)
        def handle_exception(e):
            # Handling non-HTTP exceptions only as 500
            if not(isinstance(e, HTTPException)):
                er = InternalServerError()
                er.description = str(e)
            else: er = e
            
            if isinstance(e, NotFound):
                if not request.path == '/':
                    return redirect(url_for('index'))
                else:
                    return jsonify({
                        "err":          True,
                        "code":         402,
                        "error":        'Under Maintanance',
                        "description":  'Site is under maintainance',
                    }), 402

            return jsonify({
                "err":          True,
                "code":         er.code,
                "error":        er.name,
                "url":          request.url,
                "description":  er.description,
            }), er.code

    
        # serve app for browser
        return app


# wsgi app
application = create_app()
app = create_app()
