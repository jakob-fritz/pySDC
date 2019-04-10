import numpy as np
from mpi4py import MPI
from pySDC.core.Hooks import hooks


class monitor(hooks):

    def __init__(self):
        """
        Initialization of Allen-Cahn monitoring
        """
        super(monitor, self).__init__()

        self.init_radius = None
        self.ndim = 0

    def pre_run(self, step, level_number):
        """
        Overwrite standard pre run hook

        Args:
            step (pySDC.Step.step): the current step
            level_number (int): the current level number
        """
        super(monitor, self).pre_run(step, level_number)
        L = step.levels[0]

        self.ndim = len(L.u[0].values.shape)

        c_local = np.count_nonzero(L.u[0].values > 0.0)
        comm = L.prob.pm.comm
        if comm is not None:
            c_global = comm.allreduce(sendobj=c_local, op=MPI.SUM)
        else:
            c_global = c_local
        if self.ndim == 3:
            radius = (c_global / (np.pi * 4.0 / 3.0)) ** (1.0/3.0) * L.prob.dx
        elif self.ndim == 2:
            radius = np.sqrt(c_global / np.pi) * L.prob.dx
        else:
            raise NotImplementedError('Can use this only for 2 or 3D problems')

        self.init_radius = L.prob.params.radius

        if L.time == 0.0:
            self.add_to_stats(process=step.status.slot, time=L.time, level=-1, iter=step.status.iter,
                              sweep=L.status.sweep, type='computed_radius', value=radius)
            self.add_to_stats(process=step.status.slot, time=L.time, level=-1, iter=step.status.iter,
                              sweep=L.status.sweep, type='exact_radius', value=self.init_radius)

    def post_step(self, step, level_number):
        """
        Overwrite standard post step hook

        Args:
            step (pySDC.Step.step): the current step
            level_number (int): the current level number
        """
        super(monitor, self).post_step(step, level_number)

        # some abbreviations
        L = step.levels[0]

        c_local = np.count_nonzero(L.uend.values > 0.0)
        comm = L.prob.pm.comm
        if comm is not None:
            c_global = comm.allreduce(sendobj=c_local, op=MPI.SUM)
        else:
            c_global = c_local
        if self.ndim == 3:
            radius = (c_global / (np.pi * 4.0 / 3.0)) ** (1.0 / 3.0) * L.prob.dx
        elif self.ndim == 2:
            radius = np.sqrt(c_global / np.pi) * L.prob.dx
        else:
            raise NotImplementedError('Can use this only for 2 or 3D problems')

        exact_radius = np.sqrt(max(self.init_radius ** 2 - 2.0 * (self.ndim - 1) * (L.time + L.dt), 0))

        self.add_to_stats(process=step.status.slot, time=L.time + L.dt, level=-1, iter=step.status.iter,
                          sweep=L.status.sweep, type='computed_radius', value=radius)
        self.add_to_stats(process=step.status.slot, time=L.time + L.dt, level=-1, iter=step.status.iter,
                          sweep=L.status.sweep, type='exact_radius', value=exact_radius)
