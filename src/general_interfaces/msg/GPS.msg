# The value for `fix` will be 1 if the GPS has a fix and 0 if the GPS doesn't
# have a fix. When `fix` is 0, the values for the rest of the message can be
# ignored
uint8 fix

# `satellites` specifies the number of satellites the GPS is receiving from
uint8 satellites

# Negative `latitude` indicate south while positive values indicate north
float32 latitude

# Negative `longitude` indicate west while positive values indicate east
float32 longitude
