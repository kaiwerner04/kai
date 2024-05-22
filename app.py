import os
import openai
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import logging
from datetime import datetime, timedelta
from utils import get_option_chain_dates_within_range, get_current_stock_price, get_option_premium

openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://kais-trendy-site-0e1711.webflow.io"}})
app.secret_key = 'your_secret_key'

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return 'Welcome to the Stock Hedging App', 200

@app.route('/start', methods=['POST'])
def start():
    try:
        session.clear()
        session['step'] = 1
        session['history'] = []
        logging.debug("Session started successfully.")
        return jsonify({"message": "Welcome! Let's start with the basics. What is the stock symbol of the stock you want to hedge?"})
    except Exception as e:
        logging.error(f"Error in /start: {e}")
        return jsonify({"message": f"Error: {e}"}), 500

@app.route('/next', methods=['POST'])
def next_step():
    try:
        data = request.get_json()
        user_response = data['message']
        step = session.get('step', 1)

        # Ensure session history is initialized
        if 'history' not in session:
            session['history'] = []

        session['history'].append({"role": "user", "content": user_response})
        logging.debug(f"Step: {step}, User Response: {user_response}")

        if step == 1:
            session['symbol'] = user_response.upper()
            try:
                session['current_price'] = get_current_stock_price(session['symbol'])
                session['step'] = 2
                response = "Great! How many shares do you own?"
                logging.debug(f"Valid stock symbol received: {session['symbol']}")
            except Exception as e:
                logging.error(f"Invalid stock symbol: {session['symbol']}, Error: {e}")
                response = "The stock symbol is invalid. Please enter a valid stock symbol."
        elif step == 2:
            try:
                session['num_shares'] = int(user_response)
                session['step'] = 3
                response = "Understood. What is the maximum amount you are willing to lose (in dollars)?"
                logging.debug(f"Number of shares received: {session['num_shares']}")
            except ValueError:
                logging.error(f"Invalid number of shares: {user_response}")
                response = "Please enter a valid number of shares."
        elif step == 3:
            try:
                session['loss_aversion'] = float(user_response)
                session['step'] = 4
                response = "Got it. For how many weeks would you like this hedge to be effective?"
                logging.debug(f"Loss aversion amount received: {session['loss_aversion']}")
            except ValueError:
                logging.error(f"Invalid loss aversion amount: {user_response}")
                response = "Please enter a valid amount."
        elif step == 4:
            try:
                session['hedge_duration'] = int(user_response)
                symbol = session['symbol']
                target_date = (datetime.now() + timedelta(weeks=session['hedge_duration'])).strftime("%Y-%m-%d")
                expiration_dates = get_option_chain_dates_within_range(symbol, target_date, weeks_range=2)
                session['expiration_dates'] = expiration_dates
                session['step'] = 5
                response = {
                    "message": "Here are some expiration dates close to your desired hedge duration. Please choose one of the following dates:",
                    "dates": expiration_dates
                }
                logging.debug(f"Hedge duration received: {session['hedge_duration']} weeks")
                return jsonify(response)
            except ValueError:
                logging.error(f"Invalid hedge duration: {user_response}")
                response = "Please enter a valid number of weeks."
        elif step == 5:
            session['expiration_date'] = user_response
            session['step'] = 6
            response = "Please explain your reason for wanting to hedge and whether you are bullish or bearish."
            logging.debug(f"Expiration date chosen: {session['expiration_date']}")
        elif step == 6:
            session['hedging_reason'] = user_response
            sentiment = "bullish" if "bullish" in user_response.lower() else "bearish"
            session['sentiment'] = sentiment

            prompt = (
                f"Symbol: {session['symbol']}\n"
                f"Company: {session['symbol']}\n"
                f"Current Price: {session['current_price']}\n"
                f"Hedging Reason: {session['hedging_reason']}\n"
                f"Sentiment: {session['sentiment']}\n"
                "Please research the current news and market trends regarding the company with the given symbol. Based on the above details and your research, suggest an appropriate strike price for the client."
            )
            strike_price_suggestion = send_data_to_chatgpt(prompt, context=session['history'])

            session['suggested_strike_price'] = strike_price_suggestion
            session['history'].append({"role": "assistant", "content": strike_price_suggestion})
            session['step'] = 7
            response = f"Based on your sentiment and current news, here is the suggested strike price information: {strike_price_suggestion}. What strike price would you like to use?"
            logging.debug(f"Hedging reason and sentiment received: {session['hedging_reason']}, {session['sentiment']}")
        elif step == 7:
            try:
                session['strike_price'] = float(user_response)
                session['option_type'] = 'put' if session['sentiment'] == 'bearish' else 'call'

                symbol = session['symbol']
                expiration_date = session['expiration_date']
                strike_price = session['strike_price']
                call_premium, put_premium = get_option_premium(symbol, expiration_date, strike_price)
                session['call_premium'] = call_premium
                session['put_premium'] = put_premium
                total_cost = (call_premium or 0) * session['num_shares'] + (put_premium or 0) * session['num_shares']
                additional_prompt = f"How many {session['option_type']} options should be bought to fully hedge {session['num_shares']} shares with a total premium cost of approximately ${total_cost:.2f}, show the premium per share, show the calculation process? Don't include the formulas like you write them on ChatGPT but make it easy for the API product to understand. Additionally, don't put things in bold."
                option_quantity_suggestion = send_data_to_chatgpt(additional_prompt, context=session['history'])

                session['history'].append({"role": "assistant", "content": option_quantity_suggestion})
                session['step'] = 8
                response = f"{option_quantity_suggestion}\n\nThe estimated total cost to hedge with {session['option_type']} options is approximately ${total_cost:.2f}. Do you wish to proceed with this strategy? (Yes/No, or I have questions)"
                logging.debug(f"Strike price received: {session['strike_price']}, Option type: {session['option_type']}")
            except ValueError:
                logging.error(f"Invalid strike price: {user_response}")
                response = "Please enter a valid numeric value for the strike price."
        elif step == 8:
            if user_response.lower() == 'yes':
                brokers = """
                Great! Here are some brokers where you can take these positions:
                - <a href="https://www.tdameritrade.com/">Ameritrade</a>
                - <a href="https://www.tradestation.com/">TradeStation</a>
                - <a href="https://www.interactivebrokers.com/en/home.php">Interactive Brokers</a>
                """
                response = f"{brokers} Do you need further assistance?"
                logging.debug("User agreed to proceed with the strategy.")
            elif user_response.lower() == 'no':
                session['step'] = 9
                response = "Please explain your questions or concerns."
                logging.debug("User declined to proceed with the strategy.")
            else:
                session['step'] = 9
                response = "Please explain your questions or concerns."
                logging.debug("User has questions or concerns.")
        elif step == 9:
            prompt = (
                f"User has the following questions or concerns: {user_response}\n"
                f"Provide detailed answers to help the user understand and resolve their issues."
            )
            response = send_data_to_chatgpt(prompt, context=session['history'])

            session['history'].append({"role": "assistant", "content": response})
            session['step'] = 8
            response = f"{response}\n\nDo you now understand and wish to proceed with the strategy? (Yes/No, or I have questions)"
            logging.debug(f"User questions or concerns received: {user_response}")

        session['history'].append({"role": "assistant", "content": response})
        logging.debug(f"Step {step} processed successfully with response: {response}")

        return jsonify({"message": response})
    except Exception as e:
        logging.error(f"Error in /next: {e}")
        return jsonify({"message": f"Error: {e}"}), 500

def send_data_to_chatgpt(prompt, context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *context,
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logging.error(f"Error sending data to ChatGPT: {e}")
        return f"Error: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
