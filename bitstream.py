import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import random
import noise
import os
import uuid

# https://terrafans.xyz/antenna/
# https://terraforms.oolong.lol/terraform

st.write('🐠 bitstream')

class SavedMaps:

    def __init__(self):

        path = os.getcwd()

        self.path = os.path.join(path, 'heightmaps')

        self.items = [item for item in next(os.walk(self.path))[2]]

        return
    
    def read_file_as_string(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return f"Error: The file at {file_path} was not found."
        except Exception as e:
            return f"Error: {e}"
    
    @property
    def maps(self):
        return {item:self.read_file_as_string(os.path.join(self.path, item)) for item in self.items}

if "saved_maps" not in st.session_state:
    st.session_state.saved_maps = SavedMaps().maps

saved_maps = st.session_state.saved_maps

# Function to create a preview of the selected colormap
def show_cmap_preview(cmap_name):
    # Create a gradient image to show the colormap
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack((gradient, gradient))

    fig, ax = plt.subplots(figsize=(6, 1))  # Preview size
    ax.set_title(f"Colormap: {cmap_name}")
    ax.imshow(gradient, aspect='auto', cmap=cmap_name)
    ax.set_axis_off()  # Hide axis
    st.sidebar.pyplot(fig)

# Create a function to generate the heatmap and overlay symbols
def create_heatmap_with_symbols(
        array,                     
        glyphs, 
        seed=None, 
        font_path=None, 
        figsize=(16, 16), 
        dpi=300, 
        text=None, 
        cmap='viridis',
        save:bool=True,
        save_name='heatmap_with_symbols_shifted.png',
        display_zone:bool=False):
    np.random.seed(seed)  # Ensure reproducibility with seed

    # Create a colormap for the heatmap
    cmap = plt.get_cmap(cmap)
    norm = mcolors.Normalize(vmin=0, vmax=9)

    # Calculate the shift based on the seed (to make the symbols shift predictably)
    shift = seed % len(glyphs)  # Calculate the shift based on the seed

    # Create the plot with a larger figsize
    fig, ax = plt.subplots(figsize=figsize)  # Adjusted figsize for better clarity
    
    # Display the heatmap
    cax = ax.imshow(array, cmap=cmap, norm=norm)

    # Overlay symbols based on the array values and the shift from the seed
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            symbol_idx = (array[i, j] + shift) % len(glyphs)  # Apply the shift to the array value
            symbol = Symbol(glyphs[symbol_idx], font_path=font_path)  # Pick symbol based on the shifted index
            symbol.draw(ax, j, i)

    # Remove axis labels for a clean view
    ax.axis('off')

    if text:
        ax.text(.94, -0.01, text, ha='center', va='center', fontsize=12, color='gray', transform=ax.transAxes)
    
    if display_zone:
        #ax.text(.1, -0.01, f'{"".join(glyphs)}', ha='center', va='center', fontsize=12, color='gray', fontproperties=(fm.FontProperties(fname=font_path) if font_path else None), transform=ax.transAxes)
        ax.text(.2, -0.01, f'{save_name.replace(".png","")}', ha='center', va='center', fontsize=12, color='gray', transform=ax.transAxes)

    if save:
        # Save the figure with high resolution (higher dpi)
        plt.savefig(save_name, dpi=dpi, bbox_inches='tight')  # Save image with larger resolution
    
    # Show the plot
    #plt.show()
    st.pyplot(plt)

    plt.close()

# Function to generate a 32x32 array of random values between 0 and 9
def generate_array(seed=None):
    np.random.seed(seed)  # Ensure reproducibility with seed
    return np.random.randint(0, 10, size=(32, 32))

# Define the Symbol class
class Symbol:
    def __init__(self, symbol, font_path=None):
        self.symbol = symbol
        self.font_path = font_path

    def draw(self, ax, x, y, size=14):  # Reduced font size to 10
        # If a font path is provided, use it; otherwise, default to system font
        font_properties = fm.FontProperties(fname=self.font_path) if self.font_path else None
        ax.text(x, y, self.symbol, fontsize=size, ha='center', va='center', color='black', fontproperties=font_properties)

def generate_perlin_noise(width, height, scale=10.0, octaves=6, seed=None):
    """Generates a heightmap using Perlin noise with integer values between 0 and 9."""
    shape = (width, height)
    world = np.zeros(shape)

    # Generate Perlin noise and scale it to values between 0 and 9
    for i in range(width):
        for j in range(height):
            # Generate noise value between -1 and 1
            value = noise.pnoise2(i / scale,
                                  j / scale,
                                  octaves=octaves,
                                  persistence=0.5,
                                  lacunarity=2.0,
                                  repeatx=1024,
                                  repeaty=1024,
                                  base=seed)
            # Scale the value to between 0 and 9 and ensure it's an integer
            value = (value + 1) * 4.5  # Maps -1,1 to 0,9
            value = int(value)  # Ensure it's an integer
            
            # Ensure the value is within bounds (0 to 9)
            world[i][j] = max(0, min(9, value))

    return world.astype(np.int32)  # Ensuring the array type is integer (0-9)


def string_to_heightmap(input_string, height=32, width=32, value_range=(0, 9)):
    """
    Converts a long string into a heightmap (2D array) based on character ASCII values.
    
    Parameters:
    - input_string (str): The input string to convert into a heightmap.
    - height (int): The height (rows) of the output heightmap.
    - width (int): The width (columns) of the output heightmap.
    - value_range (tuple): The range of integer values (min, max) for the heightmap (default is 0-9).
    
    Returns:
    - np.ndarray: A 2D array representing the heightmap with integer values.
    """
    
    # Convert the string to a list of ASCII values (or Unicode code points)
    ascii_values = [ord(c) for c in input_string]
    
    # If the string is too short, repeat it to fill the heightmap
    while len(ascii_values) < height * width:
        ascii_values.extend(ascii_values)  # Repeat the list until it's long enough
    
    # Trim to fit the heightmap size
    ascii_values = ascii_values[:height * width]
    
    # Convert the list of ASCII values into a 2D array (height x width)
    heightmap = np.array(ascii_values).reshape((height, width))
    
    # Map ASCII values to the specified value range (0-9 or other)
    min_val, max_val = value_range
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min()) * (max_val - min_val)
    heightmap = heightmap.astype(int)  # Ensure the values are integers
    
    return heightmap

cmap_list = ['viridis', 'cividis', 'Reds', 'PuBu', 'Greys', 'Purples', 'Blues', 'Greens', 'YlOrBr', 'YlOrRd', 'YlGnBu', 'BuGn', 'YlGn', 'PuRd', 'bone', 'pink', 'spring', 'summer', 'autumn', 'cool', 'Wistia', 'hot', 'afmhot', 'copper', 'PiYg', 'PRGn', 'Spectral', 'twilight', 'hsv', 'Dark2', 'Pastel1', 'Pastel2', 'plasma', 'inferno', 'magma', 'cividis', 'jet', 'coolwarm', 'YlGnBu', 'tab20c']
selected_cmap = st.sidebar.selectbox("Choose a colormap", cmap_list)

show_cmap_preview(selected_cmap)


text_input = st.sidebar.text_input('Custom Label', None)

tab1, tab2, tab3, tab4 = st.sidebar.tabs(['Glyphs & Font', 'Heightmap', 'Seed', 'Saving'])

show_info = tab1.toggle('Show Info', False)

manual_glyphs = tab1.toggle('Manual Glyphs', True)

if manual_glyphs:
    glyph_raw = tab1.text_input('Glyphs', '𓂧𓆑𓏏𓎛𓋴𓇋𓌳𓃀𓆗𓆀𓅱𓆠𓆉𓎡𓍯𓃥𓃣𓈖𓇋𓃢𓃦')
    glyphs_select = "Manual"
    glyphs = [i for i in glyph_raw]
else:
    glyph_table = {
        'Egyptian1': '𓂧𓆑𓏏𓎛𓋴𓇋𓌳𓃀𓆗𓆀𓅱𓆠𓆉𓎡𓍯𓃥𓃣𓈖𓇋𓃢𓃦',
        'Jackals1': '𓃢𓃦𓃥𓃣𓁢𓃤𓃧𓃨',
        'Jackals2': '𓃢𓃦𓃥𓃣',
    }
    glyph_opts = [k for k in glyph_table.keys()]
    glyphs_select = tab1.selectbox('Glyph Table', glyph_opts)
    glyphs = [i for i in glyph_table[glyphs_select]]
    tab1.code("".join(glyphs))


# Path to the Noto font (adjust as needed)
font_path = tab1.text_input('Fonts','/usr/share/fonts/truetype/noto/NotoSansEgyptianHieroglyphs-Regular.ttf')  # Adjust for your system

hm_opts = ['Unorganized', 'Noise', 'String', 'Template']

hm_select = tab2.selectbox('Heightmap', hm_opts, index=3)

randomize_seed = tab3.toggle('Randomize Seed', True)

more_noise = tab3.toggle('Shift Glyphs', False)

random_seed = random.randint(0,100000)

seed = tab3.number_input('Seed',0,100000, (random_seed if randomize_seed else 42), disabled=(True if randomize_seed else False))

save_image = tab4.toggle('Save Image', False)

name_encode = tab4.toggle('Encode Details as Name', True)

hm_inversion = tab2.toggle('Inversion', False)

hm_blend_noise = tab2.toggle('Blend Noise', False, disabled=(True if hm_select == hm_opts[1] else False))

noise_map = generate_perlin_noise(32, 32, seed=seed)

if (hm_select == hm_opts[0]):
    Heightmap = generate_array(seed)
if (hm_select == hm_opts[1]):
    Heightmap = noise_map
if (hm_select == hm_opts[2]):
    to_height = tab2.text_input('Enter String to convert to Heightmap').strip()
    Heightmap = None
    if len(to_height) != 1024:
        tab2.info('String must be 1024 characters encoded 0-9')
    else:
        Heightmap = string_to_heightmap(to_height)
if (hm_select == hm_opts[3]):
    template_select = tab2.selectbox('Select a template to use', saved_maps.keys())
    Heightmap = string_to_heightmap(saved_maps[template_select])

if hm_inversion:
    Heightmap = 9 - Heightmap  # Assuming heightmap values range from 0 to 9

if hm_blend_noise:
    Heightmap = np.where(Heightmap == 0, noise_map, Heightmap)

with st.expander('Data', icon='🛂'):
    st.code('\n'.join([' '.join(map(str, row)) for row in Heightmap]))

st.sidebar.markdown('---')
if hm_select == hm_opts[3]:
    selected_template = template_select.replace('.txt','')
else:
    selected_template = 'seed'
image_name = tab4.text_input('Image Name', (f'{hm_select}_{selected_template}_{glyphs_select}_{selected_cmap}_{seed}.png' if name_encode else 'heatmap_with_symbols_shifted.png'), disabled=(False if save_image and not name_encode else True))

st.sidebar.write(f'Saving is {"Enabled" if save_image else "Disabled"}')

if st.sidebar.button('Generate', icon='🏭'):
    create_heatmap_with_symbols(Heightmap, glyphs, seed=(random.randint(0,100000) if more_noise else seed), font_path=font_path, figsize=(16, 16), dpi=300, text=text_input, cmap=selected_cmap, save=save_image, save_name=image_name, display_zone=show_info)
