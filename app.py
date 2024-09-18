from website import create_app

#to run the application
app = create_app()
if __name__ == '__main__' :
     app.run(debug=True)


