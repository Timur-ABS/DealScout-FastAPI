from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


async def send_message(recipient, pin):
    login = "dealscouthelp@gmail.com"
    password = "dgrkbfklxfzanneh"
    # Параметры сообщения
    subject = "Your secure PIN"

    # HTML-тело сообщения
    body = f"""
   <html>
  <body>
    <div style="font-family: Arial, sans-serif; margin: 0 auto; max-width: 600px; padding: 20px 40px; color: #ffffff; background-color: #333333;">
        <div style="text-align: center;">
            <img src="https://i.postimg.cc/KjQkhByy/image-2.png" style="width: 200px;" alt="Your Logo">
            <h1 style="color: #ffffff;">Your Secure PIN</h1>
        </div>
        <div style="background-color: #444444; padding: 20px; border-radius: 8px;">
            <h2 style="color: #ffffff;">Dear Customer,</h2>
            <p style="font-size: 16px; line-height: 1.5;">Your PIN is: <strong style="color: #d93025;">{pin}</strong></p>
            <p style="font-size: 16px; line-height: 1.5;">Please keep this PIN secure and do not share it with anyone. Thank you for using our service!</p>
        </div>
        <div style="text-align: center; margin-top: 40px;">
            <p style="font-size: 14px; color: #cccccc;">This email was sent from a notification-only address that cannot accept incoming email. Please do not reply to this message.</p>
        </div>
    </div>
  </body>
</html>
    """

    # Создание MIME сообщения
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = login
    msg["To"] = recipient

    # Добавление HTML-тела после текстового
    mime_text = MIMEText(body, "html")
    msg.attach(mime_text)

    # Отправка сообщения
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(login, password)
        server.sendmail(login, recipient, msg.as_string())
        server.quit()
        return {'error': False}
    except Exception as e:
        print(e)
        return {'error': True}
