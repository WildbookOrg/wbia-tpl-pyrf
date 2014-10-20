#============================
# Python Interface
#============================
import sys
from os.path import join, isdir, realpath, dirname
import shutil
import cv2
import os
import utool
from vtool import image as gtool


def rmtreedir(path):
    if isdir(path):
        shutil.rmtree(path)


def ensuredir(path):
    utool.ensuredir(path)


def _build_shared_c_library(rebuild=False):
    if rebuild:
        repo_dir = realpath(join(dirname(__file__), '..'))
        rmtreedir(join(repo_dir, 'build'))
    retVal = os.system('./build_unix.sh')
    if retVal != 0:
        print('[rf] C Shared Library failed to compile')
        sys.exit(0)
    print('[rf] C Shared Library built')


def _prepare_inventory(directory_path, images, total, category, train=True, positive=True):
    output_fpath = directory_path + '.txt'
    output = open(output_fpath, 'w')

    if train:
        output.write(str(total) + ' 1\n')
    else:
        output.write(str(total) + '\n')

    for counter, image in enumerate(images):
        if counter % int(len(images) / 10) == 0:
            print('%0.2f' % (float(counter) / len(images)))

        filename = join(directory_path, image.filename)

        if train:
            i = 1
            cv2.imwrite(filename + '_boxes.jpg', image.show(display=False))
            for bndbox in image.bounding_boxes():
                if positive and bndbox[0] != category:
                    continue

                _filename = filename + '_' + str(i) + '.jpg'

                xmax = bndbox[1]  # max
                xmin = bndbox[2]  # xmin
                ymax = bndbox[3]  # ymax
                ymin = bndbox[4]  # ymin

                width, height = (xmax - xmin), (ymax - ymin)

                temp = cv2.imread(image.image_path())  # Load
                temp = temp[ymin:ymax, xmin:xmax]      # Crop

                target_width = 128
                if width > target_width:
                    ratio = float(height) / width
                    width = target_width
                    height = int(target_width * ratio)
                    temp = gtool.resize(temp, (width, height))

                xmax = width
                xmin = 0
                ymax = height
                ymin = 0

                if positive:
                    postfix = ' %d %d %d %d %d %d' % (xmin, ymin, xmax, ymax,
                                                        xmin + width / 2,
                                                        ymin + height / 2)
                else:
                    postfix = ' %d %d %d %d' % (xmin, ymin, xmax, ymax)

                cv2.imwrite(_filename, temp)  # Save
                output.write(_filename + postfix + '\n')
                i += 1
        else:
            postfix = ''
            cv2.imwrite(filename, cv2.imread(image.image_path()))  # Save
            output.write(filename + postfix + '\n')

    output.close()

    return output_fpath


def get_training_data_from_ibeis(dataset, category, pos_path, neg_path,
                                 val_path, test_path, test_pos_path,
                                 tast_neg_path, **kwargs):
    # How does the data look like?
    dataset.print_distribution()

    # Get all images using a specific positive set
    (pos, pos_rois), (neg, neg_rois), val, test = dataset.dataset(
        category,
        neg_exclude_categories=kwargs['neg_exclude_categories'],
        max_rois_pos=kwargs['max_rois_pos'],
        max_rois_neg=kwargs['max_rois_neg'],
    )

    raw_input("Continue...")

    print('[rf] Caching Positives')
    pos_fpath = _prepare_inventory(pos_path, pos, pos_rois, category)

    print('[rf] Caching Negatives')
    neg_fpath = _prepare_inventory(neg_path, neg, neg_rois, category, positive=False)

    print('[rf] Caching Validation')
    val_fpath  = _prepare_inventory(val_path, val, len(val), category, train=False)

    print('[rf] Caching Test')
    test_fpath = _prepare_inventory(test_path, test, len(test), category, train=False)

    print('[rf] Caching Test Positives')
    test_pos_fpath = _prepare_inventory(test_pos_path, pos, len(pos), category, train=False)

    print('[rf] Caching Test Negatives')
    test_neg_fpath = _prepare_inventory(tast_neg_path, neg, len(neg), category, train=False)

    return pos_fpath, neg_fpath, val_fpath, test_fpath, test_pos_fpath, test_neg_fpath
