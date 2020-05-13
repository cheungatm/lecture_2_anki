# Import relevant libraries
import argparse
import os
import io
import sys
from PyPDF2 import PdfFileReader, PdfFileWriter
from wand.image import Image
import pandas as pd

## convert pdf to png ##
def pdf_page_to_png(src_pdf, pagenum = 0, resolution = 72,):
    """
    Returns specified PDF page as wand.image.Image png.
    :param PyPDF2.PdfFileReader src_pdf: PDF from which to take pages.
    :param int pagenum: Page number to take.
    :param int resolution: Resolution for resulting png in DPI.
    """
    pdf_bytes = io.BytesIO()
    src_pdf.write(pdf_bytes)
    pdf_bytes.seek(0)

    img = Image(file = pdf_bytes, resolution = resolution)
    img.convert("png")

    return img


## split pdf fxn ##
def pdf_splitter(path, output):
    fname = os.path.splitext(os.path.basename(path))[0]
    # Open the file
    pdf_file = open('./{}'.format(slides_path), 'rb')
    pdf = PdfFileReader(pdf_file)
    for page in range(pdf.getNumPages()):
        pdf_writer = PdfFileWriter()
        pdf_writer.addPage(pdf.getPage(page))
        output_filename = '{}/{}_slide_{}.png'.format(output,fname, page+1)
        # with open(output_filename, 'wb') as out:
        #     pdf_writer.write(out)
        output_png = pdf_page_to_png(src_pdf = pdf_writer)
        output_png.save(filename = output_filename)
        print('Created: {}'.format(output_filename))


## Main fxn ##
if __name__ == "__main__":
    # Create the parser
    argParser = argparse.ArgumentParser(description = 'Read in files')

    # Add the arguments
    argParser.add_argument( '-S', '--slides',
                            help = 'The pdf slides for the same lecture.',
                            type = str
                            )
    
    argParser.add_argument( '-U', '--anki',
                            help = 'The Anki Profile folder to use.',
                            type = str
                            )

    argParser.add_argument('-N', '--notes',
                            help = '.csv file containing Question, Answer, and slide number as headings',
                            type = str
                            )

    argParser.add_argument('-O', '--output_path',
                            help = 'path to save output Anki csv file',
                            type = str
                            )  

    # Execute the parse_args() method
    args = argParser.parse_args()

    # Check for existence of user folder first
    print('Checking Anki user folder exists...')
    if args.anki is None:
        print('Giving a User folder is necessary.', file=sys.stderr)
        print('Requirement will soon be removed.', file=sys.stderr)
        sys.exit(-1)

    ankiPath = os.path.expanduser(args.anki)

    if not os.path.isdir(ankiPath):
        print('Folder: {} does not exist.'.format(ankiPath), file=sys.stderr)
        sys.exit(-1)

    collectionMediaPath = os.path.join(ankiPath, 'collection.media')
    if not os.path.isdir(collectionMediaPath):
        print('Folder: {} does not exist.'.format(collectionMediaPath), file=sys.stderr)
        print('Is "{}" the path to a user profile?'.format(ankiPath), file=sys.stderr)
        sys.exit(-1)

    print('Anki folder verification done.')

    if args.output_path is None:
        print('No output path provided.')
        print('Using ./ as the output path.')
        output_folder = './'
    else:
        output_folder = args.output_path

    ####### Read pdf lecture ########
    slides_path = os.path.expanduser(args.slides)
    print('Loading {}...'.format(slides_path))
    pdf_splitter(path = slides_path, output = collectionMediaPath)
    
    print('Slide splitting done.')

    ##### Create csv for Anki upload ####
    # if "notes" variable is not null
    if args.notes is None:
        print('no notes included')
    else:
        print("Notes used: {}".format(args.notes))
    # read in the csv/tsv
    notes_file = pd.read_csv(args.notes)
    # Fill in NaN values with 0
    notes_file.fillna(0, inplace = True)
    # Coerce column to integer format to ensure proper file naming later on
    notes_file['Slide_Number'] = pd.to_numeric(notes_file['Slide_Number'], downcast = 'integer')

    # extract the name of the lecture (without path or file type extension)
    lecture_title = os.path.basename(os.path.splitext(slides_path)[0])
    # rename the Slide_Number column to the correct Anki format
    notes_file['Slide_Number'] = '<img src=\"' + lecture_title + '_slide_' + notes_file['Slide_Number'].astype(str) + '.png\">'
    # Save file
    notes_file.to_csv('{}{}_QAS.csv'.format(output_folder, lecture_title), index = False, header = False)
