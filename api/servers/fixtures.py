from fixture import DataSet


class ServerData(DataSet):
    class server_01:
        name = 'analytics'
        ip = '127.0.0.1'
        folder = 'odesk-match-cloudml/analytics'
        is_default = True
