import hydra

from config import EvoConfig


def ill_cross_eval(cfg: EvoConfig, sweep_configs, sweep_params):
    breakpoint()


@hydra.main(version_base="1.3", config_path="conf", config_name="cross_eval")
def dummy_ill_cross_eval(cfg: EvoConfig):
    # Our drill_cross_eval plugin intercepts this function call to call 
    # `ill_cross_eval`
    pass


if __name__ == '__main__':
    dummy_ill_cross_eval()