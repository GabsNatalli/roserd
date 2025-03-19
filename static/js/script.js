tsParticles.load("tsparticles", {
    fpsLimit: 60,
    particles: {
        number: {
            value: 150, // Aumentei o número de partículas para criar uma rede densa
            density: {
                enable: true,
                area: 800
            }
        },
        color: {
            value: "#ff5555" // Partículas vermelhas para combinar com o tema
        },
        shape: {
            type: "circle"
        },
        opacity: {
            value: 0.5, // Opacidade média para um efeito sutil
            random: true, // Opacidade varia entre partículas
            anim: {
                enable: true,
                speed: 1, // Oscilação lenta da opacidade
                opacity_min: 0.3,
                sync: false
            }
        },
        size: {
            value: 2, // Partículas pequenas para um efeito delicado
            random: true,
            anim: {
                enable: true,
                speed: 2, // Oscilação lenta no tamanho
                size_min: 0.5,
                sync: false
            }
        },
        move: {
            enable: true,
            speed: 1, // Velocidade ajustada para um movimento mais equilibrado
            direction: "none",
            random: true,
            straight: false,
            outModes: {
                default: "out"
            },
            attract: {
                enable: false
            }
        },
        links: {
            enable: true,
            distance: 120, // Distância para formar as conexões
            color: "#ff5555", // Linhas vermelhas para combinar com o tema
            opacity: 0.2, // Linhas sutis para o efeito de teia
            width: 1
        }
    },
    interactivity: {
        events: {
            onHover: {
                enable: true,
                mode: "grab" // Conexões se intensificam ao passar o mouse
            },
            onClick: {
                enable: true,
                mode: "push" // Adiciona partículas ao clicar
            },
            resize: true
        },
        modes: {
            grab: {
                distance: 150, // Reduzi a distância para suavizar o efeito
                line_linked: {
                    opacity: 0.3 // Reduzi a opacidade das linhas ao passar o mouse
                }
            },
            push: {
                quantity: 4
            }
        }
    },
    detectRetina: true
});
