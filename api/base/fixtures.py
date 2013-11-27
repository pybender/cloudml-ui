from fixture import DataSet, SQLAlchemyFixture
from fixture.style import NamedDataStyle
 
import models
 

 
 
class SpamData(DataSet):
 
    class spam01:
        name = 'spam spam spam'
 
 
class EggData(DataSet):
 
    class egg01:
        description = 'green, for eating with mechanically separated meat'
 
 
# A simple trick for installing all fixtures from an external module.
all_data = (SpamData, EggData,)