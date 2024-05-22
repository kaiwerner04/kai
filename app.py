from flask import Flask, request, jsonify, session
import yfinance as yf
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/start', methods=['POST'])
def start():
    session['history'] = []
    logging.debug("Session started. History initialized.")
    return jsonify({"response": "Welcome! Let's start with the basics. What is the stock symbol of the stock you want to hedge?"})

@app.route('/next', methods=['POST'])
def next_step():
    user_input = request.json.get('input')
    step = len(session['history'])

    logging.debug(f"Step: {step}, User Response: {user_input}")

    if step == 0:
        session['history'].append({'step': 0, 'input': user_input})
        ticker = yf.Ticker(user_input)
        try:
            ticker.history(period="1d")
            session['ticker'] = user_input
            logging.debug(f"Valid stock symbol received: {user_input}")
            return jsonify({"response": "Great! How many shares do you own?"})
        except Exception as e:
            logging.error(f"Invalid stock symbol: {user_input}, Error: {e}")
            return jsonify({"response": "The stock symbol is invalid. Please enter a valid stock symbol."})
    elif step == 1:
        try:
            shares = int(user_input)
            session['history'].append({'step': 1, 'input': user_input})
            logging.debug(f"Number of shares received: {shares}")
            return jsonify({"response": f"Great! You own {shares} shares. What do you want to do next?"})
        except ValueError:
            logging.error(f"Invalid number of shares: {user_input}")
            return jsonify({"response": "Please enter a valid number of shares."})
    else:
        logging.debug("Unhandled step.")
        return jsonify({"response": "I'm sorry, I didn't understand that. Can you please repeat?"})

if __name__ == '__main__':
    app.run(debug=True)
