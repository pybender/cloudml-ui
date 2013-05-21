from mongokit import DocumentMigration


class ModelMigration(DocumentMigration):
    def allmigration01__add_example_id(self):
        self.target = {'example_id': {'$exists': False}}
        self.update = {'$set': {'example_id': 'application_id'}}

    def allmigration02__add_example_label(self):
        self.target = {'example_label': {'$exists': False}}
        self.update = {'$set': {'example_label': 'contractor.dev_profile_title'}}