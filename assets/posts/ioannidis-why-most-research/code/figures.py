import altair as alt
import numpy as np
from collections import namedtuple

Colors = namedtuple("Colors", ("scheme", "text", "axis", "background"))

light = Colors(["black", "green"], "black", "lightgray", "#f9f8ef")
dark = Colors(["black", "green"], "#c5c5c5", "#656466", "#0f141a")

alt.renderers.enable("browser")

def p_t_bar_a(R, beta, alpha):
    return (1 - beta) * R / (R + alpha - R * beta)

def p_not_false(R, beta):
    return (1 - beta) * R

def p_t_bar_a_u(R, beta, alpha, u):
    return ((1 - beta)*R + u*beta*R) / ((1 - beta)*R + u*beta*R + alpha + u*(1-alpha))

def p_not_false_u(R, beta, u):
    return (R*((1 - beta) + u*beta) - u) / (1 - u)

def figure1(colors: Colors, name: str):
    Rs = np.linspace(0, 1, 100) 
    alpha = 0.05
    beta = 0.2
    prob_not_false = p_not_false(Rs, beta)
    diagonal = p_not_false(Rs, 0)
    ppvs = p_t_bar_a(Rs, beta, alpha)

    source_data = list(zip(Rs, ppvs, prob_not_false)) + list(zip(Rs, p_t_bar_a(Rs, 0, alpha), diagonal))

    data = alt.Data(values=[
        *[
            {
                "alpha": alpha,
                "beta": beta,
                "R": R,
                "type": "\u03b2=0" if (R == pnf) else "\u03b2=0.2",
                "prob_not_false": pnf,
                "ppv": ppv,
            }
            for R, ppv, pnf
            in source_data
        ]
    ])


    size = dict(width=300, height=200)

    chart = alt.Chart(data).mark_line(strokeWidth=3).encode(
        x=alt.X("R:Q"),
        y=alt.Y("prob_not_false:Q", title="(1 - \u03b2) R"),
        color=alt.Color("type:N").legend(title=None),
    ).properties(**size)

    chart += alt.Chart(data).mark_line(color=colors.text, strokeDash=[5,5]).encode(
        x="R:Q", y="alpha:Q",
    )

    chart |= alt.Chart(data).mark_line(strokeWidth=3).encode(
        x=alt.X("R:Q"),
        y=alt.Y("ppv:Q", title="PPV"),
        color=alt.Color("type:N").legend(title=None, orient="top", offset=1, legendX=1),
    ).properties(**size)

    chart.configure(
        background=colors.background,
        axis=alt.Axis(gridColor=colors.axis, labelFontWeight=400, labelColor=colors.text, labelFontSize=14, labelFont="monospace", titleColor=colors.text, titleFontSize=18, titleFont="monospace"),
        legend=alt.Legend(labelFont="monospace", labelColor=colors.text, labelFontSize=18),
    ).save(f"../static/{name}.png", ppi=200)


def figure2(colors: Colors, name: str):
    Rs = np.linspace(0, 1, 100) 
    u = 0.2
    alpha = 0.05
    beta = 0.2
    prob_not_false = p_not_false_u(Rs, beta, u)
    diagonal = p_not_false(Rs, 0)
    ppvs = p_t_bar_a_u(Rs, beta, alpha, u)

    source_data = (
        list(zip(Rs, ppvs, prob_not_false)) + 
        list(zip(Rs, p_t_bar_a(Rs, 0, alpha), diagonal))
    )

    data = alt.Data(values=[
        *[
            {
                "alpha": alpha,
                "beta": beta,
                "R": R,
                "u": u,
                "type": "\u03b2=0 & u=0" if (R == pnf) else "\u03b2=0.2 & u=0.2",
                "prob_not_false": pnf,
                "ppv": ppv,
            }
            for R, ppv, pnf
            in source_data
        ]
    ])


    size = dict(width=300, height=200)

    chart = alt.Chart(data).mark_line(strokeWidth=3).encode(
        x=alt.X("R:Q"),
        y=alt.Y("prob_not_false:Q", title="When PPV > 0.5"),
        color=alt.Color("type:N").legend(title=None),
    ).properties(**size)

    chart += alt.Chart(data).mark_line(color=colors.text, strokeDash=[5,5]).encode(
        x="R:Q", y="alpha:Q",
    )

    chart |= alt.Chart(data).mark_line(strokeWidth=3).encode(
        x=alt.X("R:Q"),
        y=alt.Y("ppv:Q", title="PPV"),
        color=alt.Color("type:N").legend(title=None, orient="top", offset=1, legendX=1),
    ).properties(**size)

    chart.configure(
        background=colors.background,
        axis=alt.Axis(gridColor=colors.axis, labelFontWeight=400, labelColor=colors.text, labelFontSize=14, labelFont="monospace", titleColor=colors.text, titleFontSize=18, titleFont="monospace"),
        legend=alt.Legend(labelFont="monospace", labelColor=colors.text, labelFontSize=18),
    ).save(f"../static/{name}.png", ppi=200)

def main():
    figure1(light, "table1-light")
    figure1(dark, "table1-dark")
    figure2(light, "table2-light")
    figure2(dark, "table2-dark")

if __name__ == "__main__":
    main()
