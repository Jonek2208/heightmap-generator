"""Coordinates system transformation"""
import numpy as np

R = 6371009


def geog2ecef(point, units='deg'):
    """Geographic coordinates (lat, lon, height) to ECEF"""
    if units == 'deg':
        phi = np.deg2rad(point[0])
        lam = np.deg2rad(point[1])
    elif units == 'rad':
        phi = point[0]
        lam = point[1]
    else:
        raise Exception("Unknown units")
    height = point[2]
    coords = np.array([np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])
    return (R + height) * coords


def ecef2geog(point, units='deg'):
    """ECEF to geographic coordinates"""
    point_norm = np.linalg.norm(point)
    point /= point_norm
    height = point_norm - R
    phi = np.arcsin(point[2])
    lam = np.arctan2(point[1], point[0])
    if units == 'deg':
        phi, lam = np.rad2deg((phi, lam))
    return np.array([phi, lam, height])


def geo_dist(point1, point2, units='deg'):
    """Function returns geographic distance between two points"""
    return np.linalg.norm(geog2ecef(point1, units) - geog2ecef(point2, units))


def rot_mat(phi, lam, units='deg'):
    """Rotation matrix"""
    def rot_x(angle):
        return np.array([[1, 0, 0],
                         [0, np.cos(angle), -np.sin(angle)],
                         [0, np.sin(angle), np.cos(angle)]])

    def rot_z(angle):
        return np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0],
                         [0, 0, 1]])

    if units == 'deg':
        phi, lam = np.deg2rad((phi, lam))
    return rot_x(-np.pi / 2 + phi) @ rot_z(-np.pi / 2 - lam)


class LTP:
    """ENU local tangent plane"""

    def __init__(self, cen, units='deg'):
        self.rot_mat = rot_mat(cen[0], cen[1], units)
        self.cen = geog2ecef(cen, units)

    def from_geog(self, point, units='deg'):
        """Conversion from geographic coordinates to enu with central point in self.cen"""
        return self.rot_mat @ (geog2ecef(point, units) - self.cen)

    def to_geog(self, point, units='deg'):
        """Conversion to geographic coordinates from enu with central point in self.cen"""
        return ecef2geog(self.rot_mat.T @ point + self.cen, units)
