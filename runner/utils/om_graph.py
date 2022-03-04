import matplotlib.pyplot as plt
import numpy as np


def om_graph(opponent_model, save_path):
    if len(opponent_model) > 1:
        # plot opponent model vs. real utilities
        fig = plt.gcf()
        x = np.arange(len(opponent_model))
        real_utilities = np.vectorize(lambda x: x["utility"])(opponent_model)
        moddeled_utilities = np.round(
            np.vectorize(lambda x: x["expected_utility"])(opponent_model), 3
        )
        error = np.abs(moddeled_utilities - real_utilities)
        coef = np.polyfit(x, error, 1)
        poly1d_fn = np.poly1d(coef)
        plt.plot(x, real_utilities, c="green", label="Real")
        plt.plot(x, moddeled_utilities, c="red", label="Expected")
        plt.plot(x, poly1d_fn(x), "--k", label="Error")

        plt.xlabel("Rounds")
        plt.ylabel("Utility")
        plt.title("Opponent utility vs. expected utility model")
        plt.legend()
        fig.set_size_inches(20, 10)
        plt.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
