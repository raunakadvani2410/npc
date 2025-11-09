from flask import Flask, render_template, request, redirect, url_for, jsonify
#from main_login_ppp import OTP
import os

app = Flask(__name__)

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# # Route to handle form submission
# @app.route('/submit', methods=['POST'])
# def submit():
#     # Here you would handle the OTP, e.g., call a function to submit it
#     return redirect(url_for('home'))

# # create routes for call query example
# @app.route('/query_example')
# def query_example():
#     request
#     return 'Hello GeeksForGeeks...'

# # Route to handle form submission
# @app.route('/submit', methods=['POST', 'GET'])
# def submit():
#     otp = request.form['otp']
#     # Here you would handle the OTP, e.g., call a function to submit it
#     print(f"OTP Submitted: {otp}")
#     # return jsonify({'otp': otp})
#     return otp


# if __name__ == '__main__':
#     # app.run(debug=True)
#     app.run(debug = True, host=os.getenv('IP', '0.0.0.0'), 
#             port=int(os.getenv('PORT', 4040)))
    

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    global stored_otp
    otp = request.form.get('otp')
    if otp:
        stored_otp = otp
        print(f"OTP Submitted: {otp}")
        return f"OTP Submitted: {otp}"
    return "No OTP received", 400

# Route to get the submitted OTP
@app.route('/get_otp', methods=['GET'])
def get_otp():
    if stored_otp:
        return jsonify({'otp': stored_otp})
    return "No OTP submitted yet", 404

if __name__ == '__main__':
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 4040)))
