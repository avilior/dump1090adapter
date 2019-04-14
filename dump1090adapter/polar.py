import matplotlib.pyplot as plt
import numpy as np
import time

"""
plt.ion()

fig = plt.figure()
ax = fig.add_subplot(111)

x = [0,1,2,3]
y = [0,1,2,3]

li, = ax.plot(x, y, 'o')


fig = plt.gcf()

for i in range(100):
    try:
        x.append(i)
        y.append(i)

        li.set_xdata(x)
        li.set_ydata(y)

        ax.relim()
        ax.autoscale_view(True, True, True)

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01)
        time.sleep(0.05)

    except KeyboardInterrupt:
        plt.close('all')
        break



"""
plt.ion()
fig = plt.figure(figsize=(6,6))  # size
ax = plt.subplot(111, polar=True)

plt.grid(color='#888888')
ax.set_theta_zero_location('N') # set zero to North
ax.set_theta_direction(-1)

line1, = ax.plot([],[])

bar_colors = ['#333333', '#444444', '#555555']
num_obs = len(bar_colors)
wind_direction = (2*3.14) * (np.random.random_sample(num_obs))
wind_speed     = 5 * (np.random.random_sample(num_obs))

wind = zip(wind_direction, wind_speed, bar_colors)

for w in wind:
    ax.plot((0,w[0]), (0,w[1]), c=w[2], zorder = 3)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)
