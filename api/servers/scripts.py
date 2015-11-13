"""
This file is used for updating servers table once
"""
from api.servers.models import Server


def update_server_types():
    """
    Sets correct server type (based on name)
    """
    # set production type
    servers = Server.query.filter(Server.name.like('%Production%')).all()
    for server in servers:
        server.type = Server.PRODUCTION
        server.save()
    # set staging type
    servers = Server.query.filter(Server.name.like('%Staging%')).all()
    for server in servers:
        server.type = Server.STAGING
        server.save()