from flask import Flask, render_template, request, flash, redirect
import sqlite3
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_PATH = "library_notification.db"

# Flask-Mail Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "librarynotificationsystem@gmail.com"
app.config["MAIL_PASSWORD"] = "euzc jyry yxht blrf"
app.config["MAIL_DEFAULT_SENDER"] = ("Library Notification", "librarynotificationsystem@gmail.com")

# Initialize Flask-Mail
mail = Mail(app)

def send_email_to_patrons(patrons, title, author, genre):
    subject = "New Book Added to the Library!"
    body = (
        f"Dear Patron,\n\n"
        f"A new book titled '{title}' by '{author}' "
        f"in the genre '{genre}' has been added to the library.\n"
        f"We thought you might be interested based on your previous checkouts!\n\n"
        f"Happy reading,\nYour Library Team"
    )
    for patron in patrons:
        recipient = patron[1]  # Email field
        try:
            msg = Message(subject=subject, recipients=[recipient], body=body)
            mail.send(msg)
            print(f"Email sent to {recipient}.")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        acquisition_date = request.form["acquisition_date"]

        if not title or not author or not genre or not acquisition_date:
            flash("Please fill out all fields!", "danger")
            return redirect("/")

        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Check if the book title already exists
            cursor.execute(
                "SELECT * FROM Books WHERE Title = ?",
                (title,)
            )
            existing_book = cursor.fetchone()

            if existing_book:
                # If the book exists, show an error and do not insert
                flash(f"The book '{title}' by {author} is already in the library.", "warning")
                return redirect("/")

            # Insert the new book if it doesn't already exist
            cursor.execute(
                """
                INSERT INTO Books (Title, Author, Genre, AcquisitionDate)
                VALUES (?, ?, ?, ?)
                """,
                (title, author, genre, acquisition_date),
            )
            conn.commit()

            # Find patrons who have checked out books with the same genre
            cursor.execute(
                """
                SELECT DISTINCT Patrons.PatronID, Patrons.Email
                FROM CheckoutHistory
                JOIN Books ON CheckoutHistory.BookID = Books.BookID
                JOIN Patrons ON CheckoutHistory.PatronID = Patrons.PatronID
                WHERE Books.Genre = ?
                ORDER BY CheckoutHistory.CheckoutDate DESC
                """,
                (genre,),
            )
            patrons = cursor.fetchall()

            # Send email notifications to matching patrons
            if patrons:
                send_email_to_patrons(patrons, title, author, genre)
                flash("New book added and emails sent to relevant patrons!", "success")
            else:
                flash("New book added, but no matching patrons found.", "info")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
        finally:
            conn.close()

        return redirect("/")

    return render_template("form.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


