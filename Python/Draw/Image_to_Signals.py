from PIL import Image
import numpy as np
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib
matplotlib.use('TkAgg')

def Image_to_Objects(image_path, voltage_range):
    image = Image.open(image_path)
    if image.mode != 'RGBA':
        image = image.convert("RGBA")

    alpha_channel = np.array(image.split()[-1])

    objects = identify_objects(alpha_channel)

    voltage_objects = []
    for obj_coords in objects:
        voltage_pairs = generate_voltage_pairs_for_object(obj_coords, image.size, voltage_range)
        voltage_objects.append(voltage_pairs)

    return voltage_objects


def identify_objects(alpha_channel):
    # Applying threshold to binarize the alpha channel
    threshold_value = threshold_otsu(alpha_channel)
    binary_image = alpha_channel > threshold_value

    # Labeling the objects
    labeled_image = label(binary_image)

    # Extracting properties of each region
    props = regionprops(labeled_image)

    objects = []
    for prop in props:
        # Here, prop.coords gives us the (row, col) or (y, x) of each pixel
        objects.append(prop.coords)

    return objects


def generate_voltage_pairs_for_object(obj_coords, image_size, voltage_range):
    aspect_ratio = image_size[0] / image_size[1]

    # Ajuster voltage_range pour l'axe Y en fonction de l'aspect ratio
    voltage_range_y = voltage_range / aspect_ratio

    voltage_per_pixel_x = voltage_range / image_size[0]
    voltage_per_pixel_y = voltage_range_y / image_size[1]

    voltage_pairs = []
    for coord in obj_coords:
        y, x = coord  # Coordonnées de chaque pixel à l'intérieur de l'objet

        # Calcul direct de la tension pour chaque coordonnée, ajusté par l'aspect ratio
        vx = ((x - image_size[0] / 2) * voltage_per_pixel_x)
        vy = ((image_size[1] / 2 - y) * voltage_per_pixel_y)


        voltage_pairs.append((vx, vy))

    # Suppression des doublons
    voltage_pairs = list(set(voltage_pairs))

    return voltage_pairs


def create_grid(points):
    # Déterminez les limites de la grille
    min_x, min_y = np.min(points, axis=0)
    max_x, max_y = np.max(points, axis=0)

    # Calculez le nombre de cellules dans chaque direction
    nx = int(np.ceil((max_x - min_x)))
    ny = int(np.ceil((max_y - min_y)))

    # Assignez chaque point à une cellule
    indices = np.floor((points - np.array([min_x, min_y]))).astype(int)
    grid = {}
    for idx, point in zip(indices, points):
        grid.setdefault((idx[0], idx[1]), []).append(point)

    return grid, nx, ny, (min_x, min_y)


def Objects_path(voltage_objects):
    path = []
    for voltage_pairs in voltage_objects:
        points = np.array(voltage_pairs)
        grid, nx, ny, origin = create_grid(points)
        object_path = []
        visited = set()
        for i in range(nx):
            for j in range(ny):
                cell = (i, j)
                if cell in grid:
                    # Triez les points dans la cellule actuelle par la distance au dernier point du chemin
                    cell_points = grid[cell]
                    if object_path:
                        last_point = object_path[-1]
                        cell_points.sort(key=lambda p: np.linalg.norm(p - last_point))
                    for point in cell_points:
                        if tuple(point) not in visited:
                            object_path.append(point)
                            visited.add(tuple(point))
        path.append(object_path)

    return path


def Path_To_Signal(Objects):
    # Initialisation des listes pour stocker les signaux
    signal_lr = []
    signal_ud = []

    for Object in Objects:
        for point in Object:
            # Génération des valeurs constantes pour chaque point pendant le temps défini
            signal_lr.append(point[0])  # Notez que nous n'utilisons pas de sous-listes ici
            signal_ud.append(point[1])  # Notez que nous n'utilisons pas de sous-listes ici

    # Conversion des listes en arrays numpy 1D
    signal_lr = np.array(signal_lr)
    signal_ud = np.array(signal_ud)

    return signal_lr, signal_ud


if __name__ == '__main__':
    voltage_range = 20

    voltage_objects = Image_to_Objects('INSA.png', voltage_range)
    print("Image to objects done")

    voltage_objects_sorted = Objects_path(voltage_objects)
    print("Objects to path done")

    signal_lr, signal_ud = Path_To_Signal(voltage_objects_sorted)
    print("Path to signal done")

    """# Plotting all objects part
    plt.figure()
    colors = cm.rainbow(np.linspace(0, 1, len(voltage_objects)))  # Generating colors

    for obj_idx, sorted_voltage_pairs in enumerate(voltage_objects_sorted):
        voltage_pairs_x, voltage_pairs_y = zip(*sorted_voltage_pairs)
        plt.scatter(voltage_pairs_x, voltage_pairs_y, s=1, color=colors[obj_idx])

    voltage_pairs_x, voltage_pairs_y = zip(*sorted_voltage_pairs)
    plt.scatter(voltage_pairs_x, voltage_pairs_y, s=1, color=colors[0])

    plt.title('Voltage Map for Non-transparent Pixels per Object')
    plt.xlabel('V_x (Voltage for X coordinate)')
    plt.ylabel('V_y (Voltage for Y coordinate)')
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

    # Plotting objects paths one by one part
    for obj_idx, object_path in enumerate(voltage_objects_sorted):
        plt.figure()
        voltage_pairs_x, voltage_pairs_y = zip(*object_path)
        plt.plot(voltage_pairs_x, voltage_pairs_y, '-o', markersize=1, linewidth=0.5)
        plt.title(f"Chemin pour l'objet {obj_idx + 1}")
        plt.xlabel('V_x (Voltage for X coordinate)')
        plt.ylabel('V_y (Voltage for Y coordinate)')
        plt.grid(True)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()"""

    # Plotting path
    all_points = [point for object_path in voltage_objects_sorted for point in object_path]
    # Extraire les coordonnées x et y
    all_x_coords, all_y_coords = zip(*all_points)

    plt.figure()  # Vous pouvez ajuster la taille si nécessaire
    plt.plot(all_x_coords, all_y_coords, '-o', markersize=1, linewidth=0.5, color='blue')

    plt.title('Chemin complet')
    plt.xlabel('V_x (Voltage for X coordinate)')
    plt.ylabel('V_y (Voltage for Y coordinate)')
    plt.grid(True)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

    # Plotting signals part
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))
    # Configuration du titre et des labels des axes pour le premier subplot
    ax[0].set_title('Signal Left-Right (LR)')
    ax[0].set_xlabel('Sample Number')
    ax[0].set_ylabel('Voltage')
    # Tracé du signal LR
    ax[0].plot(signal_lr)

    # Configuration du titre et des labels des axes pour le deuxième subplot
    ax[1].set_title('Signal Up-Down (UD)')
    ax[1].set_xlabel('Sample Number')
    ax[1].set_ylabel('Voltage')
    # Tracé du signal UD
    ax[1].plot(signal_ud)

    plt.tight_layout()
    plt.show()

