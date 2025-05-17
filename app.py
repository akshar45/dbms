
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["LibraryDB"]
books = db["Books"]
students = db["Students"]
issued_books = db["IssuedBooks"]

@app.route("/")
def index():
    available_books = books.find()
    return render_template("index.html", books=available_books)

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        title = request.form["title"]
        author = request.form["author"]
        total_copies = int(request.form["total_copies"])
        books.insert_one({
            "BookID": book_id,
            "Title": title,
            "Author": author,
            "TotalCopies": total_copies,
            "AvailableCopies": total_copies
        })
        return redirect(url_for("index"))
    return render_template("add_book.html")

@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        student_id = int(request.form["student_id"])
        name = request.form["name"]
        department = request.form["department"]
        students.insert_one({
            "StudentID": student_id,
            "Name": name,
            "Department": department
        })
        return redirect(url_for("index"))
    return render_template("register_student.html")

@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        student_id = int(request.form["student_id"])
        book = books.find_one({"BookID": book_id})
        if book and book["AvailableCopies"] > 0:
            issued_books.insert_one({
                "BookID": book_id,
                "StudentID": student_id,
                "IssueDate": datetime.now(),
                "ReturnDate": None
            })
            books.update_one({"BookID": book_id}, {"$inc": {"AvailableCopies": -1}})
        return redirect(url_for("index"))
    return render_template("issue_book.html")

@app.route("/return_book", methods=["GET", "POST"])
def return_book():
    if request.method == "POST":
        issue_id = request.form["issue_id"]
        issue = issued_books.find_one({"_id": ObjectId(issue_id)})
        if issue and not issue["ReturnDate"]:
            issued_books.update_one({"_id": ObjectId(issue_id)}, {"$set": {"ReturnDate": datetime.now()}})
            books.update_one({"BookID": issue["BookID"]}, {"$inc": {"AvailableCopies": 1}})
        return redirect(url_for("issued_books_view"))
    # Show all unreturned books
    unreturned = issued_books.find({"ReturnDate": None})
    return render_template("return_book.html", records=unreturned)

@app.route("/issued_books")
def issued_books_view():
    data = issued_books.find()
    return render_template("issued_books.html", issued=data)

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    results = books.find({
        "$or": [
            {"Title": {"$regex": query, "$options": "i"}},
            {"Author": {"$regex": query, "$options": "i"}}
        ]
    })
    return render_template("search_results.html", results=results, query=query)

if __name__ == "__main__":
    app.run(debug=True)
