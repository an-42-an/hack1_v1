# library_app.py

from flask import *
from flask_login import LoginManager, UserMixin, login_required, login_user,\
    logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from argon2 import PasswordHasher
argon2 = PasswordHasher()
from datetime import *

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#argon2 = Argon2(app)
app=Flask(__name__)
app.secret_key = "any key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.secret_key = "any key"
db=SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

def time_diff(date1: date, time1: time, date2: date, time2: time) -> float:
    dt1 = datetime.combine(date1, time1)
    dt2 = datetime.combine(date2, time2)
    return (dt2 - dt1).total_seconds() / 3600
# ------------------ DATABASE MODELS ------------------

class User(db.Model,UserMixin):
    username = db.Column(db.String(80), primary_key=True)
    passwd_hash = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    #lib_id = db.Column(db.Integer, db.ForeignKey('library.lib_id'))
    def get_id(self):
        return self.username
class Library(db.Model):
    lib_id=db.Column(db.Integer,  autoincrement=True, primary_key=True )
    name = db.Column(db.String(80))
    address = db.Column(db.String(300))
    location = db.Column(db.String(100))
    shelves = db.Column(db.Integer)
    contact = db.Column(db.String(15))
class Shelf(db.Model):
    lib_id = db.Column(db.Integer, db.ForeignKey('library.lib_id'))
    shelf_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookname = db.Column(db.String(100))
    cost = db.Column(db.Integer)

class BookReview(db.Model):
    rev_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'))
    book_id = db.Column(db.String(100), db.ForeignKey('book.book_id'))
    library = db.Column(db.String(80), db.ForeignKey('library.lib_id'))
    rating = db.Column(db.Integer,nullable=False)
    comments = db.Column(db.Text)

class LibReview(db.Model):
    rev_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'))
    lib_id = db.Column(db.String(80), db.ForeignKey('library.lib_id'))
    comments = db.Column(db.Text)
    rating = db.Column(db.Integer, nullable=False)

class Reservation(db.Model):
    res_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'))
    book = db.Column(db.String(100), db.ForeignKey('book.book_id'))
    lib_id = db.Column(db.String(80), db.ForeignKey('library.lib_id'))
    reserved_at = db.Column(db.DateTime, default=datetime.now)
    confirmed = db.Column(db.Boolean, default=False)

# ------------------ ROUTES ------------------
@login_manager.user_loader
def load_user(id):
    return User.query.filter_by(username=id).first()
@app.route('/')
def home():
    return render_template('index.html',flag='user' not in session)
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    else:
        user=request.form.get('Username')
        arg=User.query.filter_by(username=user).first()
        pwd=request.form.get('Password')
        print(user,pwd)
        try:
            if argon2.verify(arg.passwd_hash,pwd):
                login_user(arg)
                return redirect('/')
        except Exception as e:
            print(f"Error verifying password: {e}")
            return render_template('login.html', msg="Invalid credentials. Enter correct details")
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')
@app.route('/searchbooks', methods=['GET', 'POST'])
def searchbooks():
    if request.method=='GET':
        books=Book.query.all()
    else:
        i=request.form.get('i').strip()
        books=Book.query.filter(Book.bookname.ilike(f"%{i}%")).all()
    return render_template('searchbooks.html', books=books)
@app.route('/searchlib', methods=['GET', 'POST'])
def searchlib():
    if request.method=='GET':
        libs = Library.query.all()
    else:
        i=request.form.get('i').strip()
        libs = Library.query.filter((Library.name.ilike(f"%{i}%")) | (Library.location.ilike(f"%{i}%"))).all()
    return render_template('searchlib.html', libs=libs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = argon2.hash(request.form['password'])
        db.session.add(User(username=request.form['username'], \
                                passwd_hash=hashed, type='user'))
            
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/newlib', methods=['GET', 'POST'])
def newlib():
    if request.method=='POST':
        name = request.form['name']
        address = request.form['address']
        location = request.form['location']
        shelves = int(request.form['shelves'])
        password = request.form['password']
        contact=request.form['contact']
        l=Library(name=name,address=address,location=location,\
                               shelves=shelves,contact=contact)
        db.session.add(l)
        db.session.commit()
        #print(l.lib_id)
        db.session.add(User(username=l.lib_id,passwd_hash=argon2.hash(password),type='lib'))
        db.session.commit()
        
        for a in range(shelves):
            db.session.add(Shelf(lib_id=l.lib_id))
        db.session.commit()
        return redirect('/login')
    return render_template('newlib.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)