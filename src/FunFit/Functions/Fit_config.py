FIT_PRESETS = {
    "Polynomials": ["N", "A<sub>1</sub>", "c"],
    "Exponential": ["A", "b", "c"],
    "Quasicrystal": ["N", "A<sub>1</sub>", "λ<sub>1</sub>", "φ<sub>1</sub>", "θ", "x0", "y0", "c"],
    "Fourier series": ["N", "A<sub>1</sub>", "λ<sub>1</sub>", "φ<sub>1</sub>", "θ", "c"],
    "Gaussian": ["A", "µ_x", "µ_y", "σ_x", "σ_y", "c"],
    "Custom": []
}

FIT_EQUATIONS = {
    "Polynomials": r"$Z = c + \sum_{n=1}^N A_n x^{n}$",
    "Exponential": r"$Z = A e^{bx} + c$",
    "Gaussian": r"$Z = A e^{-\left(\frac{(x-\mu_x)^2}{2\sigma_x^2} + \frac{(y-\mu_y)^2}{2\sigma_y^2}\right)} + c$",
    "Quasicrystal": r"$Z = \sum_{n=1}^N A_n \cos\left(\frac{2\pi}{\lambda_n}\left[x\cos\theta_n + y\sin\theta_n\right] + \phi_n\right) + c$",
    "Fourier series": r"$Z = \sum_{n=1}^N A_n \cos\left(\frac{2\pi}{\lambda_n}x + \phi_n\right) + c$",
    "Custom": ""
}
