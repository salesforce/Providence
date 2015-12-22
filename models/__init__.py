'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
Base = declarative_base()
from sqlalchemy.dialects.postgresql import JSONB, JSON

class Plugin(Base):
    __tablename__ = 'plugin'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    last_attempted_run = Column(DateTime)
    last_successful_run = Column(DateTime)
    type = Column(String(50))
    documents = relationship("PluginDocument", backref="plugin")
    __table_args__ = (
        UniqueConstraint('name'),
    )

class Repo(Base):
    __tablename__ = 'repo'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    last_attempted_run = Column(DateTime)
    last_successful_run = Column(DateTime)
    last_identifier = Column(String())
    documents = relationship("RepoDocument", backref="repo")
    __table_args__ = (
        UniqueConstraint('name'),
    )

class Document(Base):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    data = Column(JSONB)
    text = Column(Text())
    __table_args__ = (
        UniqueConstraint('name'),
    )

class RepoDocument(Base):
    __tablename__ = 'repo_document'
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repo.id'))
    name = Column(String())
    data = Column(JSONB)
    text = Column(Text())
    tool = Column(String(50))
    date = Column(DateTime(timezone=True))
    counter = Column(Integer)
    __table_args__ = (
        UniqueConstraint('repo_id','tool','name'),
    )

class PluginDocument(Base):
    __tablename__ = 'plugin_document'
    id = Column(Integer, primary_key=True)
    plugin_id = Column(Integer, ForeignKey('plugin.id'))
    name = Column(String())
    data = Column(JSONB)
    text = Column(Text())
    date = Column(DateTime(timezone=True))
    counter = Column(Integer)
    __table_args__ = (
        UniqueConstraint('name','plugin_id'),
    )
