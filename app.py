from datetime import datetime
import os
import re
import urllib.request
from flask import *
import sqlite3
from werkzeug.utils import secure_filename

from web3 import Web3
app = Flask(__name__)
app.secret_key = "secret key"
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = 'any random string'
UPLOAD_FOLDER = 'static/upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.route("/")
def first():
    return render_template("first.html")


@app.route("/first")
def index():
    return render_template("index.html")


@app.route('/logon')
def logon():
    return render_template('signup.html')


@app.route("/signup", methods=["post", "get"])
def signup():
    username = request.form['user']
    name = request.form['name']
    email = request.form['email']
    number = request.form["mobile"]
    address = request.form["address"]
    private = request.form['private_key']
    password = ""
    role = "student"
    con = sqlite3.connect('crowdfunding.db')

    cur = con.cursor()
    cur.execute("insert into `userid` (`user`,`email`, `password`,`mobile`,`name`,address,privatekey) VALUES ( ?, ?, ?, ?,?,?,?)",
                (username, email, password, number, name, address, private))
    con.commit()
    session["mobile"] = number
    con.close()
    return redirect("/first")


@app.route("/userlogin")
def userlogin():
    users = session['username']
    return render_template("success.html", users=users)
    


@app.route('/logout')
def home():
    session.pop('username', None)
    return render_template("index.html")


@app.route("/mobileotp", methods=["POST"])
def mobileotp():
    import random as rd
    otp = str(rd.randint(0000, 9999))
    print(otp)
    import requests
    mobile = session["mobile"]
    session["otp"] = otp
    url = 'https://www.fast2sms.com/dev/bulkV2?authorization=xv2Z1X4jYGSJcURzBFwnWusMDq7PpkCg6HblLNrIT9O8tVAhKf9YvmuJZViftd5bQPD3alwG4hzLg1cA&route=otp&variables_values=' + \
        str(otp)+'&flash=0&numbers='+str(mobile)
    print(url)
    requests.get(url)
    return render_template("student.html")


@app.route("/check", methods=["POST", "GET"])
def check():
    otp = session["otp"]
    sotp = request.form['user']

    if (otp == sotp):
        users = session['username']
        return render_template("success.html", users=users)
    else:
        return render_template("student.html")


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    con = sqlite3.connect('crowdfunding.db')
    data = con.execute(
        "select * from userid ").fetchall()
    return render_template("admin.html", data=data)


@app.route('/crowdfunding', methods=['GET', 'POST'])
def crowdfunding():
    if request.method == 'POST':
        eventname = request.form['eventname']
        datetimefrom = request.form['datetimefrom']
        datetimeto = request.form['datetimeto']
        description = request.form['description']
        total = request.form['total']
        userid = request.form['userid']
        # Save crowdfunding data to the database
        conn = sqlite3.connect('crowdfunding.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO crowdfunding (eventname, datetimefrom, datetimeto, description, totalrequired, userid,total)
                          VALUES (?, ?, ?, ?, ?, (select userid from userid where address=?),?)''', (eventname, datetimefrom, datetimeto, description, total, userid, 0))
        conn.commit()
        conn.close()
        eventid = cursor.lastrowid
        # Handle image uploads
        files = request.files.getlist("file")

        # Iterate for each file in the files List, and Save them
        for file in files:
            file.save("static/uploads/"+file.filename)
            conn = sqlite3.connect('crowdfunding.db')
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO crowdimage (eventid, image) VALUES (?, ?)''', (eventid, file.filename))
            conn.commit()
            conn.close()
        return redirect(url_for('uploadfil'))

    return render_template('crowdfunding.html')


@app.route("/uploadfil", methods=["POST", "GET"])
def uploadfil():
    users = session['username']
    return render_template("success.html", users=users)



@app.route('/viewfund')
def viewfund():
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()

    # Fetch crowdfunding events with the associated username and filter unmet goals
    cursor.execute('''
        SELECT crowdfunding.*, userid.user 
        FROM crowdfunding 
        JOIN userid ON crowdfunding.userid = userid.userid 
        WHERE (crowdfunding.totalrequired - crowdfunding.total) >= 1 
        ORDER BY crowdfunding.eventid DESC
    ''')
    crowdfunding_data = cursor.fetchall()

    data = []
    for k in crowdfunding_data:
        event_id = k[0]
        # Fetch images for each event
        cursor.execute('SELECT * FROM crowdimage WHERE eventid = ?', (event_id,))
        crowd_img = cursor.fetchall()

        k = list(k)
        k.append(crowd_img)  # Add image list
        data.append(k)

    # Get current logged-in user's ID
    cursor.execute('SELECT userid FROM userid WHERE address = ?', (session["username"],))
    user_id = cursor.fetchone()[0]

    conn.close()
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('crowdfunding.html', crowdfunding_data=data, current_date=current_date, id=user_id)


@app.route('/yourfund')
def yourfund():
    # Connect to the database
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()

    # Fetch crowdfunding events with their images
    cursor.execute('''SELECT * FROM crowdfunding ORDER BY eventid DESC''')
    crowdfunding_data = cursor.fetchall()
    data = []
    for k in crowdfunding_data:
        cursor = conn.cursor()
        # Fetch crowdfunding events with their images
        cursor.execute(
            '''SELECT * FROM crowdimage where eventid="%s"''' % (k[0]))
        crowd_img = cursor.fetchall()
        # Close the connection

        k = list(k)
        k.append(crowd_img)
        data.append(k)
    print(data)
    cursor = conn.cursor()
    # Fetch crowdfunding events with their images
    cursor.execute('''SELECT userid FROM userid where address="%s"''' %
                   (session["username"]))
    id = cursor.fetchone()[0]
    print(id)

    conn.close()

    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template('yourfund.html', crowdfunding_data=data, current_date=current_date, id=id)


@app.route('/viewfundtransaction', methods=["POST", "GET"])
def viewfundtransaction():
    event_id = request.args.get('id')

    # Connect to the database
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()

    # Fetch transactions along with username and user ID
    cursor.execute('''
        SELECT ct.ctid, ct.amount, u.userid, u.user, ct.remark, ct.transactiondate, ct.eventid
        FROM crowdfundingtranscanction ct
        JOIN userid u ON ct.userid = u.userid
        WHERE ct.eventid = ?
        ORDER BY ct.transactiondate DESC
    ''', (event_id,))
    crowdfunding_data = cursor.fetchall()
    
    conn.close()

    return render_template('crowdfundingfund.html', crowdfunding_data=crowdfunding_data)


@app.route("/deleteuser", methods=["POST", "GET"])
def deleteuser():
    i = request.args.get('a')
    mydb = sqlite3.connect('crowdfunding.db')
    mycursor = mydb.cursor()
    tx = "delete from userid where userid={0}".format(i)
    mycursor.execute(tx)
    mydb.commit()
    mydb.close()
    return redirect("admin")


@app.route("/approveuser", methods=["POST", "GET"])
def approveuser():
    i = request.args.get('a')
    mydb = sqlite3.connect('crowdfunding.db')
    mycursor = mydb.cursor()
    tx = "update userid set approve={0} where userid={1}".format(1, i)
    mycursor.execute(tx)
    mydb.commit()
    mydb.close()
    return redirect("admin")


@app.route('/deletemultilingual', methods=['POST', "GET"])
def deletemultilingual():
    a = request.args.get('a')
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute("delete from multilingual where mid=?", [a])
    conn.commit()
    conn.close()
    return redirect("viewfund")


@app.route("/getapprove", methods=["POST", "GET"])
def getapprove():
    i = request.args.get('a')
    from web3 import Web3

    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"  # Update with your Ganache URL
    web3 = Web3(Web3.HTTPProvider(ganache_url))

    # Check connection
    if web3.is_connected():
        print("Connected to Ganache")
    else:
        print("Failed to connect to Ganache")

    acc = {}
    # Retrieve account balances
    accounts = web3.eth.accounts
    for account in accounts:
        if account != session["username"]:
            balance = web3.eth.get_balance(account)
            acc[account] = float(web3.from_wei(balance, "ether"))
    balances = acc
    # Sort the dictionary by balance in descending order
    sorted_balances = sorted(
        balances.items(), key=lambda x: x[1], reverse=True)

    # Get the top 3 balances
    top_3_balances = sorted_balances[:3]

    print("Top 3 balances:")
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute(
        'select count(*) from multilingual where eventid="%s" ' % (i))
    xid = cursor.fetchone()[0]
    if (xid == 0):
        for address, balance in top_3_balances:
            print(f"Address: {address}, Balance: {balance}")
            try:
                cursor.execute(
                    'select mid from multilingual order by mid desc limit 1')
                mid = cursor.fetchone()[0]+1
            except:
                mid = 1
            # Insert data into the users table
            try:
                cursor.execute(
                    '''INSERT INTO multilingual (mid,eventid,address,isapproved)values(?,?,?,?)''', (mid, i, address, 0))
                # Commit the transaction
                conn.commit()

            except Exception as e:
                return jsonify({'error': str(e)}), 400
        conn.close()
        return redirect("yourfund")
    return redirect("yourfund")


@app.route('/Approvemultilingual')
def Approvemultilingual():
    i = request.args.get('a')
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            '''update multilingual set isapproved= ?,approvedate= ?where mid=?''', (1, current_datetime_str, i))
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("yourfund")
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route("/pendingapprove", methods=["POST", "GET"])
def pendingapproval():
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()

    query = """
    SELECT 
        m.mid,
        m.eventid,
        c.eventname,
        u.user AS username,
        u.name AS fullname,
        m.address,
        m.privatekey,
        m.isapproved,
        m.requestdate,
        m.approvedate,
        m.isapproved
    FROM 
        multilingual m
    JOIN 
        crowdfunding c ON m.eventid = c.eventid
    JOIN 
        userid u ON c.userid = u.userid  where m.address='%s'
    """%(session['username'])

    cursor.execute(query)
    records = cursor.fetchall()

    return render_template('viewmultilingualus.html', data=records, column=[
        'mid', 'eventid', 'eventname', 'username', 'fullname',
        'address', 'privatekey', 'isapproved', 'requestdate', 'approvedate'
    ])
    

@app.route("/viewstatus", methods=["POST", "GET"])
def viewstatusl():
    i = request.args.get('a')
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    k = "select * from multilingual where eventid='%s'" % (
        i)
    cursor.execute(k)
    users = cursor.fetchall()
    return render_template('viewmultilingual.html', data=users, column=['mid', 'eventid', 'address', 'privatekey', 'isapproved', 'requestdate', 'approvedate'])


@app.route("/deletefund", methods=["POST", "GET"])
def deletefund():
    i = request.args.get('id')
    mydb = sqlite3.connect('crowdfunding.db')
    mycursor = mydb.cursor()
    tx = "delete from crowdfunding where eventid={0}".format(i)

    mycursor.execute(tx)

    mycursor = mydb.cursor()
    tx = "delete from crowdimage where eventid={0}".format(i)
    mycursor.execute(tx)

    mydb.commit()
    mydb.close()
    return redirect("viewfund")


def transfer_eth(sender_address, sender_private_key, receiver_address, amount):
    # Connect to Ethereum node (ganache or similar)
    # Update with your Ethereum node URL
    w3 = Web3(Web3.HTTPProvider('HTTP://127.0.0.1:7545'))
    # w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Convert Ether amount to Wei (1 Ether = 10^18 Wei)

    amount_wei = w3.to_wei(amount, 'ether')

    # Get nonce
    nonce = w3.eth.get_transaction_count(sender_address)

    # Build transaction
    transaction = {
        'to': receiver_address,
        'value': amount_wei,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': 1337  # Update with your chain ID
    }

    # Get nonce
    nonce = w3.eth.get_transaction_count(sender_address)

    # Build transaction
    transaction = {
        'to': receiver_address,
        'value': amount_wei,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': 1337  # Update with your chain ID
    }

    # Sign transaction
    signed_tx = w3.eth.account.sign_transaction(
        transaction, private_key=sender_private_key)

    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Store transaction receipt in SQLite database
    conn = sqlite3.connect('crowdfunding.db')
    try:
        y = conn.execute(
            "select id from transaction_receipts order by id desc").fetchone()[0] + 1
    except TypeError:  # When no records are found
        y = 1

    insert_query = """
    INSERT INTO transaction_receipts (
        id, transaction_hash, block_hash, block_number,
        cumulative_gas_used, gas_used, timestamp, sender_address, receiver_address, amount
    ) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
    """ % (
        y,
        tx_receipt.transactionHash.hex(),
        tx_receipt.blockHash.hex(),
        tx_receipt.blockNumber,
        tx_receipt.cumulativeGasUsed,
        tx_receipt.gasUsed,
        datetime.now(),
        sender_address,
        receiver_address,
        amount
    )

    conn.execute(insert_query)
    conn.commit()
    conn.close()

    print("Transaction successful")


@app.route('/insert_transaction', methods=['POST'])
def insert_transaction():
    amount = request.form['amount']
    userid = request.form['userid']
    eventid = request.form['eventid']
    remark = request.form['remark']
    transactiondate = request.form['transactiondate']

    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute(
        "select totalrequired-total from crowdfunding where eventid='%s'" % (eventid))
    amountrequired = cursor.fetchone()[0]
    
    if (amountrequired-int(amount))>=0 :
        cursor = conn.cursor()
        cursor.execute(
            "select address from userid where userid=(select userid from crowdfunding where eventid='%s')" % (eventid))
        receiver_address = cursor.fetchone()[0]
        transfer_eth(session["username"], session["privatekey"],
                    receiver_address, amount)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO crowdfundingtranscanction (amount, userid, remark, transactiondate,eventid) 
                        VALUES (?, (select userid from userid where address=?), ?, ?,?)''', (amount, userid, remark, transactiondate, eventid))

        d = "update crowdfunding set total =total+'%s' where eventid='%s'" % (
            amount, eventid)
        mycursor = conn.cursor()
        mycursor.execute(d)
        conn.commit()
        conn.close()
    return redirect("viewfund")


@app.route('/checklogin', methods=['POST'])
def checklogin():
    user = request.form['user']
    pas = request.form['password']
    if user == 'admin' and pas == 'admin':
        session['username'] = "admin"
        return redirect("admin")
    else:
        from web3 import Web3
        from web3.auto import w3

        # Connect to Ganache
        ganache_url = "http://127.0.0.1:7545"  # Update with your Ganache URL
        web3 = Web3(Web3.HTTPProvider(ganache_url))

        # Check connection
        if web3.is_connected():
            print("Connected to Ganache")
        else:
            print("Failed to connect to Ganache")

        # Get the account address associated with the private key
        account_address = w3.eth.account.from_key(pas).address
        if (account_address == user):
            print("Account Address:", account_address)
            # Retrieve the account balance
            balance = web3.eth.get_balance(account_address)
            balance_in_eth = web3.from_wei(balance, 'ether')
            print("Account Balance:", balance_in_eth, "ETH")
            con = sqlite3.connect('crowdfunding.db')
            data = 0
            data = con.execute(
                "select count(*) from userid where address = ? AND privatekey = ?", (user, pas)).fetchone()
            print(data[0])
            if data[0] != 0:
                data = con.execute(
                    "select mobile,name from userid where address = ? AND privatekey = ?", (user, pas)).fetchone()
                session['username'] = user
                session['privatekey'] = pas
                session['mobile'] = data[0]
                session['name'] = data[1]
                return redirect("userlogin")
            else:
                session['username'] = user
                session['privatekey'] = pas
                return redirect("logon")

        else:
            return redirect("/first")


@app.route('/insertchat1')
def insertchat1():
    return render_template('insertchat.html')


@app.route('/insertchat', methods=['POST'])
def insertchat():
    # Extract data from the form
    sender_address = request.form['sender_address']
    receiver_address = request.form['receiver_address']
    message = request.form['message']
    transdate = request.form['transdate']

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    try:
        cursor.execute('select cid from chat order by cid desc limit 1')
        cid = cursor.fetchone()[0]+1
    except:
        cid = 1

    # Insert data into the users table
    try:
        cursor.execute('''INSERT INTO chat (cid,sender_address,receiver_address,message,transdate)values(?,?,?,?,?)''',
                       (cid, sender_address, receiver_address, message, transdate))
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("insertchat1")
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/viewchat')
def viewchat():
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute("select * from chat where sender_address='%s' or receiver_address='%s'" %
                   (session["username"], session["username"]))
    users = cursor.fetchall()
    return render_template('viewchat.html', data=users, column=['cid', 'sender_address', 'receiver_address', 'message', 'transdate'])


@app.route('/deletechat', methods=['POST', "GET"])
def deletechat():
    a = request.args.get('a')
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute("delete from chat where cid=?", [a])
    conn.commit()
    conn.close()
    return redirect("viewchat")


@app.route('/updatechat1')
def updatechat1():
    cid = request.form.get('cid')
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()
    cursor.execute("select * from cid where cid=?", [cid])
    n = cursor.fetchone()

    return render_template('updatechat.html', n=n)


@app.route('/updatechat', methods=['POST'])
def updatechat():
    # Extract data from the form
    cid = request.form['cid']
    sender_address = request.form['sender_address']
    receiver_address = request.form['receiver_address']
    message = request.form['message']
    transdate = request.form['transdate']

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('crowdfunding.db')
    cursor = conn.cursor()

    # Insert data into the users table
    try:
        cursor.execute('''update users set sender_address= ?,receiver_address= ?,message= ?,transdate= ?where cid=?''',
                       (sender_address, receiver_address, message, transdate, cid))
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("viewchat")
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
