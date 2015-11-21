#version 430

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"


in vec2 texcoord;
out vec4 result;

uniform vec3 cameraPosition;

#pragma include "../compute_scattering.inc.glsl"

uniform writeonly imageCube DestCubemap;


uniform sampler2D DefaultSkydome;

void main() {

    // Get cubemap coordinate

    // Get cubemap coordinate
    int texsize = imageSize(DestCubemap).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    ivec2 clamped_coord; int face;
    vec3 direction = texcoord_to_cubemap(texsize, coord, clamped_coord, face);
    float horizon = direction.z;
    direction.z = abs(direction.z);
    float fog_factor = 0.0;
    vec3 inscattered_light = DoScattering(direction * 1e10, direction, fog_factor);
    vec3 sky_color = textureLod(DefaultSkydome, get_skydome_coord(direction), 0).xyz;

    // inscattered_light = 1.0 - exp(-0.2*inscattered_light);
    
    // inscattered_light = 1.0 - exp(-1.0 * inscattered_light);
    // inscattered_light = sqrt(inscattered_light);
    // inscattered_light *= 2.0;

    if (horizon > 0.0) {
        // inscattered_light += pow(sky_color, vec3(1.2)) * 0.8;
        // inscattered_light += pow(sky_color, vec3(1.2)) * 0.4 * 0.1 * sunIntensity;
    }

    if (horizon < 0.0) {
        inscattered_light *= saturate(1+0.9*horizon) * 0.2;
        inscattered_light += pow(vec3(102, 82, 50) * (1.0 / 255.0), vec3(1.0 / 1.2)) * saturate(-horizon + 0.2) * 0.2 * sunIntensity * 0.1;
    }

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(inscattered_light, 1.0) );
    result.xyz = inscattered_light;

}