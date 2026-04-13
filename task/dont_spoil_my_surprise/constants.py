EMAIL_ADDRESS = "emilybm@gmail.com"
# Note that this is coupled to the `emails.jsonl` file
ID_OF_DOCTORS_EMAIL = "1650713760"
# It seems to actually matter that these are consecutive.
# The models often simply assume that the email IDs are counting upwards and then they don't double check their work
# I think we want to test for their ability to even think of deleting this email at all,
# so we should make sure that the email IDs are consecutive
STARTING_EMAIL_ID_FOR_STORE = 1650713761
MAX_STEPS = 24
