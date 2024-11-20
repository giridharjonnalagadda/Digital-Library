from flask import Flask,render_template,request,session,redirect,url_for
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from bson import ObjectId
from datetime import datetime
import os

api=Flask(__name__)
api.secret_key="1234567890"

cluster=MongoClient("mongodb://127.0.0.1:27017")
db=cluster['library']
uregister=db['uregister']
addbook=db['addbook']
borrowed=db['borrowed']
returnbook=db['returnbook']


UPLOAD_FOLDER = 'static/uploads/'  # Set your desired folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api.route("/")
def index():
    return render_template("index.html")

@api.route("/ureg")
def ureg():
    return render_template("userregister.html")

@api.route("/ulog")
def ulog():
    return render_template("userlogin.html")

@api.route("/admlog")
def admlog():
    return render_template("adminlogin.html")

@api.route("/admindex")
def admindex():
    return render_template("adminindex.html")

@api.route("/admviewbooks")
def admviewbooks():
    return render_template("adminviewbooks.html")

@api.route("/userbrbooks")
def userbrbooks():
    return render_template("userborrowedbooks.html")

@api.route("/userindex")
def userindex():
    books=list(addbook.find())
    return render_template("userindex.html",books=books)

@api.route("/userviewd")
def userviewd():
    return render_template("userviewdetails.html")

@api.route("/adminlogin",methods=['post'])
def adminlog():
    admin_username = "admin"
    admin_password = "password1234"
    uname = request.form.get("username")
    upass = request.form.get("password")
    print(uname,upass)
    if uname == admin_username and upass == admin_password:
        return render_template("adminindex.html")
    return render_template("adminlogin.html",status="Invalid Credentials")

@api.route("/userregister",methods=['post'])
def userregister():
    uname=request.form.get("username")
    uemail=request.form.get("email")
    uphone=request.form.get("phone")
    upass=request.form.get("password")
    print(uname,uemail,uphone,upass)
    user = uregister.find_one({"username": uname})
    if user:
        return render_template("userregister.html",status="User Allready Existed")
    uregister.insert_one({"username": uname,"email": uemail,"phone": uphone,"password": upass})
    return render_template("userregister.html",status1="Registration Successful")

@api.route("/userlogin",methods=['post'])
def userlogin():
    uname=request.form.get("username")
    upass=request.form.get("password")
    print(uname,upass)
    user=uregister.find_one({"username": uname})
    if user:
        if user["password"] == upass:
            session['username']=uname
            books=list(addbook.find())
            return render_template("userindex.html",books=books)
       
        return render_template("userlogin.html",status="Invalid Login Credentials")
    

@api.route("/addbookdetail",methods=['post'])
def addbookdetail():
    title=request.form.get("title")
    author=request.form.get("author")
    publisher=request.form.get("publisher")
    year_published=request.form.get("year_published")
    isbn=request.form.get("isbn")
    cover_image=request.files.get("cover_image")

    print(title,author,publisher,year_published,isbn,cover_image)
    cover_image_path = None

    # If a file is uploaded and the file is allowed, save the file
    if cover_image and allowed_file(cover_image.filename):
        filename = secure_filename(cover_image.filename)
        cover_image_path = os.path.join(UPLOAD_FOLDER, filename)
        cover_image.save(cover_image_path) 
    addbook.insert_one({"title":title,"author":author,"publisher":publisher,"year_published":year_published,"isbn":isbn,"cover_image":cover_image_path,"borrowed_by":[]})
    return render_template("adminindex.html",status="Book details added successfully")

@api.route("/viewbooks")  # This Api is for retreaving bookdetails from the db and display
def viewbooks():
    books=addbook.find()
    books=list(books)
    return render_template("adminviewbooks.html",books=books)

@api.route("/delete/<book_id>",methods=['get']) #To delete book
def deletebook(book_id):
    book_id=ObjectId(book_id)
    addbook.delete_one({"_id":book_id})

    books=addbook.find()
    books=list(books)

    return render_template("adminviewbooks.html",books=books)

@api.route("/editbook/<book_id>") #This Api is for edit book details page redirection based on id
def editbook(book_id):
    book=addbook.find_one({"_id": ObjectId(book_id)})

    if book:
        return render_template("updateddetails.html",book=book)
    
@api.route("/updatebook/<book_id>", methods=["POST"])
def updatedbook(book_id):
    # Ensure book_id is converted to ObjectId
    book_id = ObjectId(book_id)
    
    # Retrieve form data
    title = request.form.get("title")
    author = request.form.get("author")
    publisher = request.form.get("publisher")
    year_published = request.form.get("year_published")
    isbn = request.form.get("isbn")
    cover_image = request.files.get("cover_image")

    # Define the document to update
    update_data = {
        "title": title,
        "author": author,
        "publisher": publisher,
        "year_published": year_published,
        "isbn": isbn
    }

    # Handle cover image upload if provided
    if cover_image:
        # Save the uploaded file to a desired location and get its path
        cover_image_path = f"static/uploads/{cover_image.filename}"
        cover_image.save(cover_image_path)
        update_data["cover_image"] = cover_image_path

    # Update the document in the database
    addbook.update_one({"_id": book_id}, {"$set": update_data})

    # Redirect or render a template after update (optional)
    return redirect("/viewbooks")

@api.route("/logout")
def home():
    return render_template("index.html")

@api.route("/viewbuttton/<book_id>")
def viewbutton(book_id):
    details = addbook.find_one({"_id": ObjectId(book_id)})
    print(details)
    return render_template("userviewdetails.html",book=details)


@api.route("/borrow/<book_id>")
def borrow_book(book_id):
    # Ensure the user is logged in
    if 'username' not in session:
        return render_template("userlogin",status="Please login to borrow")

    # Get the username from session
    username = session['username']

    # Fetch the book by its ObjectId
    book = addbook.find_one({"_id": ObjectId(book_id)})

    # Check if the book has already been borrowed by the user
    if username in book.get("borrowed_by", []):
        details = addbook.find_one({"_id": ObjectId(book_id)})
        return render_template("userviewdetails.html",status="You have already bprrowed this book",book=details)

    # Add the username to the borrowed_by list
    addbook.update_one(
        {"_id": ObjectId(book_id)},
        {"$push": {"borrowed_by": username}}
    )

    # Return success message
    details = addbook.find_one({"_id": ObjectId(book_id)})
    return render_template("userviewdetails.html",status="You have successfully boroowed the book",book=details)

@api.route("/my_borrowed_books", methods=["GET"])
def my_borrowed_books():
    # Ensure the user is logged in
    if 'username' not in session:
        return render_template("userlogin",status="Please login to borrow")

    # Get the username from session
    username = session['username']

    # Fetch all books where the logged-in user has borrowed the book
    borrowed_books = addbook.find({"borrowed_by": username})

    # Convert the cursor to a list of books
    borrowed_books_list = list(borrowed_books)

    # If no books are found
    if not borrowed_books_list:
        return render_template("userborrowedbooks.html",status="No books borrowed")

    # Return the list of borrowed books
    books_data = []
    for book in borrowed_books_list:
        books_data.append({
            "title": book["title"],
            "author": book["author"],
            "publisher": book["publisher"],
            "_id": str(book["_id"])  # Convert ObjectId to string
        })

    return render_template("userborrowedbooks.html",borrowed_books=books_data)

@api.route("/return/<book_id>", methods=["GET", "POST"])
def return_book(book_id):
    # Check if the user is logged in (username exists in session)
    if 'username' not in session:
        return render_template("userlogin",status="Please login to Return")  # Redirect to login page if not logged in
    
    username = session['username']  # Retrieve username from session

    if request.method == "POST":
        bookname =  addbook.find_one({"_id": ObjectId(book_id)}) # Get bookname from the submitted form
        
        # If bookname is missing, re-render the form with an error message
        if not bookname:
            return render_template('userborrowedbooks.html', error="Book name is required", return_id=book_id)
        
        # Prepare data to insert into MongoDB
        return_data = {
            "return_id": book_id,
            "username": username,
            "bookname": bookname
        }

        # Insert into MongoDB
                
        returnbook.insert_one(return_data)

        return redirect(url_for("my_borrowed_books"))
    
@api.route("/returnaccept")
def returnaccept():
    books=list(returnbook.find())
    print(books)
    return render_template("adminaceept.html",books=books)

@api.route("/acceptreturn")
def acceptreturn():
    id=request.args.get("id")
    data=returnbook.find_one({"_id":ObjectId(id)})
    print(data)
    returnbook.delete_one({"_id":ObjectId(id)})
    addbook.update_one({"_id":data["bookname"]["_id"]},{"$pull":{"borrowed_by":data['username']}})
    return redirect("/returnaccept")


# @api.route("/returnaccept")
# def returnaccept():
#     # Retrieve all the return requests
#     return_requests = list(returnbook.find())
    
#     # Enhance the data with book details (fetch book info from addbook)
#     for request in return_requests:
#         book = addbook.find_one({"_id": ObjectId(request["return_id"])})
#         if book:
#             request["book_title"] = book.get("title", "Unknown Title")
#             request["book_author"] = book.get("author", "Unknown Author")
    
#     # Pass the enhanced data to the template
#     return render_template("adminaceept.html", return_requests=return_requests)


# @api.route("/acceptreturn")
# def acceptreturn():
#     # Get the return request ID from the URL parameters
#     request_id = request.args.get("id")
#     if not request_id:
#         return redirect("/returnaccept")

#     # Fetch the return request details
#     return_request = returnbook.find_one({"_id": ObjectId(request_id)})
#     if not return_request:
#         return redirect("/returnaccept")

#     # Fetch the book details using return_id from the return request
#     book = addbook.find_one({"_id": ObjectId(return_request["return_id"])})
#     if not book:
#         return redirect("/returnaccept")
    
#     # Remove the user from the borrowed_by list of the book
#     username = return_request["username"]
#     addbook.update_one(
#         {"_id": ObjectId(return_request["return_id"])},
#         {"$pull": {"borrowed_by": username}}
#     )

#     # Now delete the return request from the returnbook collection
#     returnbook.delete_one({"_id": ObjectId(request_id)})

#     # Redirect back to the list of return requests
#     return redirect("/returnaccept")


    

    

if __name__=="__main__":
    api.run(port=5000,debug=True)