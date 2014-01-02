from fixture import DataSet


class UserData(DataSet):
    class user_01:  # token 123
        uid = u"somebody"
        name = u"User-1"
        odesk_url = "http://www.odesk.com/"
        email = u"somebody@fake.org"
        portrait_32_img = "http://www.odesk.com/"
        auth_token = "78d8045d684abd2eece923758f3cd781489df3a48e1278982466017f"

    class user_02:  # token token
        uid = u"user"
        name = u"User-2"
        odesk_url = "http://www.odesk.com/"
        email = u"user@fake.org"
        portrait_32_img = "http://www.odesk.com/"
        auth_token = "3f9aa9e0493a8850c147349134b981e92fa136b822dbc6bcc559c7d3"
