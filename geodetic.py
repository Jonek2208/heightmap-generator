"""Coordinates system transformation"""
import numpy as np

R = 6371009

def geog2ecef(v, units='rad'):
    """Geographic coordinates (lat, lon, height) to ECEF"""
    if units == 'deg':
        phi = np.deg2rad(v[0])
        lam = np.deg2rad(v[1])
    elif units == 'rad':
        phi = v[0]
        lam = v[1]
    else:
        raise Exception("Unknown units")
    h = v[2]
    z = np.sin(phi)
    y = np.cos(phi) * np.sin(lam)
    x = np.cos(phi) * np.cos(lam)
    return (R + h) * np.array([x, y, z])


def ecef2geog(v, units='deg'):
    """ECEF to geographic coordinates"""
    v_norm = np.linalg.norm(v)
    v /= v_norm
    h = v_norm - R
    phi = np.arcsin(v[2])
    lam = np.arctan2(v[1], v[0])
    if units == 'deg':
        phi, lam = np.rad2deg((phi, lam))
    return np.array([phi, lam, h])

def geo_dist(point1, point2, units='rad'):
    return np.linalg.norm(geog2ecef(point1, units) - geog2ecef(point2, units))

def rot_mat(phi, lam, units='rad'):
    """Rotation matrix"""
    def rot_x(th):
        return np.array([[1, 0, 0], [0, np.cos(th), -np.sin(th)], [0, np.sin(th), np.cos(th)]])

    def rot_z(th):
        return np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])

    if units == 'deg':
        phi, lam = np.deg2rad((phi, lam))
    return rot_x(-np.pi / 2 + phi) @ rot_z(-np.pi / 2 - lam)


class LTP:
    """ENU local tangent plane"""

    def __init__(self, cen, units='rad'):
        self.rot_mat = rot_mat(cen[0], cen[1], units)
        self.cen = geog2ecef(cen, units)

    def from_geog(self, p, units='rad'):
        """Conversion from geographic coordinates to enu with central point in self.cen"""
        return self.rot_mat @ (geog2ecef(p, units) - self.cen)

    def to_geog(self, p, units='deg'):
        """Conversion to geographic coordinates from enu with central point in self.cen"""
        return ecef2geog(self.rot_mat.T @ p + self.cen, units)
