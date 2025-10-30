import config
import machine
import usocket
import ustruct
import utime

def last_sunday(year, month):
    # Find the date of the last Sunday in a given month
    for day in range(31, 0, -1):
        try:
            t = utime.mktime((year, month, day, 0, 0, 0, 0, 0))
            if utime.localtime(t)[6] == 6:
                return day
        except:
            continue
    return 31  # fallback

def is_dst(year, month, day, hour=0):
    # DST active: last Sunday in March 01:00 → last Sunday in October 01:00
    march_sun = last_sunday(year, 3)
    oct_sun = last_sunday(year, 10)
    dst_start = utime.mktime((year, 3, march_sun, 1, 0, 0, 0, 0))
    dst_end = utime.mktime((year, 10, oct_sun, 1, 0, 0, 0, 0))
    t = utime.mktime((year, month, day, hour, 0, 0, 0, 0))
    return dst_start <= t < dst_end

def setTime():
    ntpHost = config.ntp_host
    query = bytearray(48)
    query[0] = 0x1B
    address = usocket.getaddrinfo(ntpHost, 123)[0][-1]
    sock = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
    try:
        sock.settimeout(2)
        sock.sendto(query, address)
        message = sock.recv(48)
    except Exception as e:
        print("NTP error:", e)
        machine.reset()
    finally:
        sock.close()

    now = ustruct.unpack("!I", message[40:44])[0]
    delta = 2208988800  # NTP to Unix epoch
    unix_time = int(now - delta)

    offset_hours = int(config.utc_offset)
    local = utime.gmtime(unix_time + offset_hours * 3600)
    if is_dst(local[0], local[1], local[2], local[3]):
        offset_hours += 1  # Add one hour for DST

    local = utime.gmtime(unix_time + offset_hours * 3600)
    # RTC datetime tuple format: (year, month, day, weekday, hour, minute, second, subseconds)
    machine.RTC().datetime((local[0], local[1], local[2], local[6] + 1,
                            local[3], local[4], local[5], 0))

