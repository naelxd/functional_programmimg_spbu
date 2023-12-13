import multiprocessing
import os
import cv2
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog as fd

Image.MAX_IMAGE_PIXELS = 933120000

def process_image_chunk(chunk, output_folder):
    image_path, chunk_index, chunk_data = chunk

    img = cv2.imread(image_path)

    result_chunk, contours = find_stars_in_chunk(img, chunk_data)

    output_path = os.path.join(output_folder, f"output_{os.path.basename(image_path)}_{chunk_index}.png")
    cv2.imwrite(output_path, result_chunk)

    # Сохранение местоположения объектов
    obj_locations = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        obj_locations.append((x + chunk_data[0], y + chunk_data[1], w, h))

    return {"chunk_index": chunk_index, "output_path": output_path, "obj_locations": obj_locations}



def find_stars_in_chunk(image, chunk_data):
    x_start, y_start, x_end, y_end = chunk_data
    chunk = image[y_start:y_end, x_start:x_end]

    # Преобразование изображения в оттенки серого
    gray = cv2.cvtColor(chunk, cv2.COLOR_BGR2GRAY)

    # Применение фильтра для улучшения контраста
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # Применение алгоритма выделения звезд
    _, thresholded = cv2.threshold(enhanced, 200, 255, cv2.THRESH_BINARY)

    # Нахождение контуров
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        cv2.drawContours(chunk, [contour], 0, (0, 255, 0), 2)

    return chunk, contours


def divide_image(image_path, num_chunks):
    img = Image.open(image_path)
    width, height = img.size
    chunk_size = width // num_chunks

    chunks = []
    for i in range(num_chunks):
        x_start = i * chunk_size
        x_end = (i + 1) * chunk_size if i < num_chunks - 1 else width
        chunks.append((x_start, 0, x_end, height))

    return [(image_path, i, chunk) for i, chunk in enumerate(chunks)]


def parallel_process_images(image_paths, output_folder, 
                            num_processes, num_chunks_per_image):
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_image_chunk, [(chunk, output_folder) for image_path in image_paths
                                                      for chunk in divide_image(image_path, num_chunks_per_image)])

    obj_locations = []
    img_results = []
    for result in results:
        print(f"Chunk: {result['chunk_index']}, Output: {result['output_path']}")
        img = cv2.imread(result['output_path'])
        if not(img_results) or img.shape == img_results[0].shape and img.dtype == img_results[0].dtype:
            img_results.append(img)
        else:
            print(f"Skipping {result['output_path']} due to different size or data type.")
        obj_locations += [(os.path.basename(result['output_path']), loc) for loc in result['obj_locations']]
    

    result = cv2.hconcat(img_results)

    output_path = os.path.join(output_folder, 'result.jpg')
    cv2.imwrite(output_path, result)
    print(f"Result saved to {output_path}")

    cv2.imshow('Result', result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Сохранение местоположения объектов в файл
    n_elements = 0
    with open(os.path.join(output_folder, 'obj_locations.txt'), 'w') as f:
        for image_path, loc in obj_locations:
            f.write(f"{os.path.basename(image_path)}: x={loc[0]}, y={loc[1]}, w={loc[2]}, h={loc[3]}\n")
            n_elements += 1
    print(f"Object locations saved to {os.path.join(output_folder, 'obj_locations.txt')}")

    return results, n_elements



def find_btn():
    output_folder = "result/"
    num_processes = multiprocessing.cpu_count()

    if chunks_entry.get():
        chunks = int(chunks_entry.get())
    else:
         chunks = 20

    images = fd.askopenfilenames(filetypes=[('jpg', '*.jpg')])

    results, n_elements = parallel_process_images(images, output_folder, num_processes, chunks)
    n_elements_label.config(text=f"Found {n_elements} objects")



if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('200x200')
    root.title("find obj")

    chunks_label = tk.Label(root, text="chunks")
    chunks_label.grid(row=1, column=1)
    chunks_entry = tk.Entry(root)
    chunks_entry.grid(row=1, column=2)

    n_elements_label = tk.Label(root, text="")
    n_elements_label.grid(row=4, column=1)

    btn1 = tk.Button(root, text="find", command=find_btn)
    btn1.grid(row=3, column=1)

    root.mainloop()
