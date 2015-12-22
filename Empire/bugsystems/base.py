'''
Copyright (c) 2015, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of Salesforce.com nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

"""
Base classes defining default bug & system behavior to be inherited by specific system
classes
"""

from datetime import datetime
import pytz
import hashlib

__copyright__ = "2015 Salesforce.com, Inc"
__status__    = "Prototype"

class BugSystem(object):
    def __init__(self, creds):
        pass

    def bugs_for(self, email=None, team=None):
        """ Bugs for a certain user """
        pass

    def bugs_touched_recently(self, days_ago=7):
        pass

    def bugs_open_in_period(self, from_date=None, to_date=None):
        # default from 2 years ago to today
        pass

    def bugs_closed_in_period(self, from_date=None, to_date=None):
        raise NotImplementedError

    def open_bugs(self,p0=True,p1=True,p2=True):
        """ Returns open p0/p1/p2 bugs """
        pass

class Bug(object):
    OPS_GROUP = "ops"
    PRODUCT_GROUP = "product"
    def __init__(self, id=None, title=None, rating=None, area=None, cloud=None, team=None, email=None, 
                       open_date=None, closed_date=None, url=None):
        self.cloud = cloud
        self.area = area
        self.id = id
        self.status = None        
        self.title = title
        self.email = email
        self.team = team
        self.rating = rating
        self.open_date = open_date
        self.updated_date = None
        self.closed_date = closed_date
        self.url = url
        self.group = None

    def __getattribute__(self, name):
        if name=="priority":
            return self.rating
        else:
            return object.__getattribute__(self, name)

    def time_open(self):
        if self.closed_date is None:
            return None
        return self.closed_date - self.open_date

    def age(self, at_date=None):
        if at_date is None:
            at_date = self.closed_date
        else:
            if self.closed_date is not None and self.closed_date < at_date:
                at_date = self.closed_date
        if at_date is None:
            now_aware = pytz.utc.localize(datetime.utcnow())
            return now_aware - self.open_date
        return at_date - self.open_date

    def titles(self):
        return ["cloud","area","team","group",
                "id","title","rating","status","age","email",
                "open date","closed date","url"]

    def list(self, json=False):
        open_date = self.open_date
        closed_date = self.closed_date
        age = self.age().days
        if (json is True):
            open_date = str(open_date)
            closed_date = str(closed_date)
            age = str(age)
        return [self.cloud, self.area, self.team, self.group,
                self.id, self.title, self.rating, self.status, age, self.email, 
                open_date, closed_date, self.url]

    def dictionary(self):
        dictionary = dict(zip(self.titles(), self.list()))
        return dictionary

    def json(self):
        dictionary = dict(zip(self.titles(), self.list(json=True)))
        return dictionary

    def tracking_record(self):
        def hash(data):
            return hashlib.sha224(data).hexdigest()
        return {"Title":hash(self.title),
                "Priority":self.priority,
                "Owner":self.email,
                "Group":self.group,
                "Team":self.team,
                "Status":self.status,
                "id":self.id
        }

