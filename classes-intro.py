class Kettle(object):

    def __init__(self, make, price):
        self.make = make
        self.price = price
        self.on = False

    def switch(self):
        if not self.on:
            self.on = True
        else:
            self.on = False


kenwood = Kettle("Kenwood", 8.99)
print(kenwood.make)
print(kenwood.price)

hamilton = Kettle("Hamilton", 14.55)
print(hamilton.make)
print(hamilton.price)

print("Models: {0.make} = {0.price}, {1.make} = {1.price}".format(kenwood, hamilton))

print("Hamilton: ", hamilton.on)
hamilton.switch()
print("Hamilton: ", hamilton.on)

Kettle.switch(kenwood)
print("Kenwood: ", kenwood.on)

Kettle.switch(kenwood)
print("Kenwood: ", kenwood.on)
