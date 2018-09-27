import datetime


def CreateLogEntry(user, message):
    """
    Creates a Log entry that is saved into a activity.log text file
    :param user:
    :param message:
    :return: null
    """
    log_file = open('hnet/activity.log', 'a')
    log_file.write(
        "" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ", " + str(user) + ", " + message + "\n")


def readLog():
    log = []
    file = open('HNet/activity.log', 'r')
    for line in file:
        log.append(line)
    return log
