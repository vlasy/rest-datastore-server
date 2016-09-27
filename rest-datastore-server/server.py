from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.validation import ValidatorSQL
from eve_sqlalchemy.decorators import registerSchema
from flask_security import UserMixin, RoleMixin, \
    Security, SQLAlchemyUserDatastore
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey, \
    DateTime, Table, Boolean
from sqlalchemy import func
from flask import request
import json

Base = declarative_base()

role_user = Table('role_user', Base.metadata,
                  Column('role_id', Integer, ForeignKey('role.id')),
                  Column('user_id', Integer, ForeignKey('user.id')))


class Common(Base):
    __abstract__ = True
    _created = Column(DateTime, default=func.now())
    _updated = Column(DateTime, default=func.now(), onupdate=func.now())
    _etag = Column(String(40))


class Role(Common, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(127), unique=True)
    description = Column(String(255))
    users = relationship("User", secondary=role_user, back_populates="roles")


class User(Common, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime)
    roles = relationship(Role, secondary=role_user, back_populates="users")

registerSchema('role')(Role)
registerSchema('user')(User)

settings = {
    'ID_FIELD': 'id',
    'ITEM_LOOKUP_FIELD': 'id',
    'DOMAIN': {
        'role': Role._eve_schema['role'],
        'user': User._eve_schema['user']
    },
    'ITEM_METHODS': ['GET', 'DELETE', 'PUT', 'PATCH'],
    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'DEBUG': True,
    'SQLALCHEMY_DATABASE_URI': 'postgres://postgres:root@localhost:5432/rest',
    'IF_MATCH': False,
    'ENFORCE_IF_MATCH': False,
    'EMBEDDING': True
}
settings['DOMAIN']['role']['additional_lookup'] = {
    'url': 'regex("[\w]+")',
    'field': 'name'
}

susers = settings['DOMAIN']['user']

susers['item_lookup_field'] = 'id'
settings['DOMAIN']['role']['item_lookup_field'] = 'id'

susers['embedded_fields'] = ['roles']
susers['schema']['roles']['data_relation']['embeddable'] = True


app = Eve(validator=ValidatorSQL, data=SQL, settings=settings)
db = app.data.driver


@app.route('/user/<user_id>/roles', methods=['POST'])
def add_role(user_id):
    user = db.session.query(User).get(user_id)
    # TODO: assumes that id of role is sent as well - safer verison could help
    role = db.session.query(Role).get(request.json['id'])
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()
    return json.dumps({'success': True}), 200, \
        {'ContentType': 'application/json'}


@app.route('/user/<user_id>/roles', methods=['DELETE'])
def delete_role(user_id):
    user = db.session.query(User).get(user_id)
    # TODO: assumes that id of role is sent as well - safer verison could help
    role = db.session.query(Role).get(request.json['id'])
    user.roles.remove(role)
    db.session.add(user)
    db.session.commit()
    return json.dumps({'success': True}), 200, \
        {'ContentType': 'application/json'}


Base.metadata.bind = db.engine
db.Model = Base
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


db.drop_all()
db.create_all()

if __name__ == '__main__':
    app.run()
