// 
// Modified subset of pcsx soft gpu functions. 
// For z-buffer rasterization.
//

/***************************************************************************
                          soft.c  -  description
                             -------------------
    begin                : Sun Oct 28 2001
    copyright            : (C) 2001 by Pete Bernert
    web                  : www.pbernert.com   
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version. See also the license.txt file for *
 *   additional informations.                                              *
 *                                                                         *
 ***************************************************************************/

#include "soft.h"

// from externals.h
#define FALSE 0
#define TRUE  1
#define BOOL unsigned short

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

////////////////////////////////////////////////////////////////////////////////////
// soft globals
////////////////////////////////////////////////////////////////////////////////////

short DrawSemiTrans = FALSE;
short Ymin;
short Ymax;

short ly0, lx0, lz0, ly1, lx1, lz1, ly2, lx2, lz2, ly3, lx3, lz3;   // global psx vertex coords

typedef struct SOFTVTAG
{
 int x,y,z;
} soft_vertex;

static soft_vertex vtx[4];
static soft_vertex * left_array[4], * right_array[4];
static int left_section, right_section;
static int left_section_height, right_section_height;
static int left_x, delta_left_x, right_x, delta_right_x;
static int left_z, delta_left_z, right_z, delta_right_z;
float right_zf, delta_right_zf;

short drawW=1024; short drawH=512;
short drawX=0; short drawY=0;

soft_z psxZbuf[513*1024];

#ifdef _MSC_VER

#pragma warning  (disable : 4035)

static __inline int shl10idiv(int x, int y)
{
 __asm
  {
   mov   eax,x
   mov   ebx,y
   mov   edx, eax
   shl   eax, 10
   sar   edx, 22
   idiv  ebx
   // return result in eax
  }
}

#else

static __inline int shl10idiv(int x, int y)
{
 long long int bi=x;
 bi<<=10;
 return (int)(bi/y);
}

#endif

static __inline int RightSection_Z(void)
{
 soft_vertex * v1 = right_array[ right_section ];
 soft_vertex * v2 = right_array[ right_section-1 ];

 int height = v2->y - v1->y;
 if(height == 0) return 0;
 delta_right_x = (v2->x - v1->x) / height;
 right_x = v1->x;

 right_section_height = height;
 return height;
}

static __inline int LeftSection_Z(void)
{
 soft_vertex * v1 = left_array[ left_section ];
 soft_vertex * v2 = left_array[ left_section-1 ];

 int height = v2->y - v1->y;
 if(height == 0) return 0;
 delta_left_x = (v2->x - v1->x) / height;
 left_x = v1->x;

 delta_left_z = ((v2->z - v1->z)) / height;
 left_z = v1->z;

 left_section_height = height;
 return height;  
}

static __inline BOOL NextRow_Z(void)
{
 if(--left_section_height<=0) 
  {
   if(--left_section <= 0) {return TRUE;}
   if(LeftSection_Z()  <= 0) {return TRUE;}
  }
 else
  {
   left_x += delta_left_x;
   left_z += delta_left_z;
  }

 if(--right_section_height<=0) 
  {
   if(--right_section<=0) {return TRUE;}
   if(RightSection_Z() <=0) {return TRUE;}
  }
 else
  {
   right_x += delta_right_x;
  }
 return FALSE;
}

static __inline BOOL SetupSections_Z(short x1, short y1, short z1, short x2, short y2, short z2, short x3, short y3, short z3)
{
 soft_vertex * v1, * v2, * v3;
 int height, longest, temp;
 float longestf, tempf;

 v1 = vtx;   v1->x=x1<<16;v1->y=y1;v1->z=z1;
 v2 = vtx+1; v2->x=x2<<16;v2->y=y2;v2->z=z2;
 v3 = vtx+2; v3->x=x3<<16;v3->y=y3;v3->z=z3;

 if(v1->y > v2->y) { soft_vertex * v = v1; v1 = v2; v2 = v; }
 if(v1->y > v3->y) { soft_vertex * v = v1; v1 = v3; v3 = v; }
 if(v2->y > v3->y) { soft_vertex * v = v2; v2 = v3; v3 = v; }

 height = v3->y - v1->y;
 if(height == 0) {return FALSE;}
 temp=(((v2->y - v1->y) << 16) / height);
 longest = temp * ((v3->x - v1->x)>>16) + (v1->x - v2->x);
 if(longest == 0) {return FALSE;}

 if(longest < 0)
  {
   right_array[0] = v3;
   right_array[1] = v2;
   right_array[2] = v1;
   right_section  = 2;
   left_array[0]  = v3;
   left_array[1]  = v1;
   left_section   = 1;

   if(LeftSection_Z() <= 0) return FALSE;
   if(RightSection_Z() <= 0)
    {
     right_section--;
     if(RightSection_Z() <= 0) return FALSE;
    }
   if(longest > -0x1000) longest = -0x1000;   
  }
 else
  {
   left_array[0]  = v3;
   left_array[1]  = v2;
   left_array[2]  = v1;
   left_section   = 2;
   right_array[0] = v3;
   right_array[1] = v1;
   right_section  = 1;

   if(RightSection_Z() <= 0) return FALSE;
   if(LeftSection_Z() <= 0)
    {    
     left_section--;
     if(LeftSection_Z() <= 0) return FALSE;
    }
   if(longest < 0x1000) longest = 0x1000;
  }

 Ymin=v1->y;
 Ymax=min(v3->y-1,drawH);
 
 delta_right_z=shl10idiv(temp*((v3->z - v1->z)>>10)+((v1->z - v2->z)<<6),longest);
 
 tempf = ((float)(v2->y - v1->y) / height);
 longestf = (tempf * (v3->x - v1->x)) + (float)(v1->x - v2->x);
 delta_right_zf=((tempf*(v3->z - v1->z))+(float)(v1->z - v2->z))/longestf;
 
 return TRUE;
}

static __inline void drawPoly3Zi(short x1, short y1, short z1, short x2, short y2, short z2, short x3, short y3, short z3, int id)
{
 int i,j,xmin,xmax,ymin,ymax;
 int Z,difZ;
 float Zf,difZf;
 soft_z *zn;
 if(x1>drawW && x2>drawW && x3>drawW) return;
 if(y1>drawH && y2>drawH && y3>drawH) return;
 if(x1<drawX && x2<drawX && x3<drawX) return;
 if(y1<drawY && y2<drawY && y3<drawY) return;
 if(drawY>=drawH) return;
 if(drawX>=drawW) return; 

 if(!SetupSections_Z(x1,y1,z1,x2,y2,z2,x3,y3,z3)) return;

 ymax=Ymax;

 for(ymin=Ymin;ymin<drawY;ymin++)
  if(NextRow_Z()) return;

 difZ=delta_right_z;
 difZf=delta_right_zf;
 if(/*!bCheckMask && */!DrawSemiTrans)
  {
   // color |=sSetMask;
   for (i=ymin;i<=ymax;i++)
    {
     xmin=left_x >> 16;
     xmax=(right_x >> 16)-1; if(drawW<xmax) xmax=drawW;

     if(xmax>=xmin)
      {
       Z=left_z;
       Zf=(float)left_z;

       if(xmin<drawX)
        {j=drawX-xmin;xmin=drawX;Z+=j*difZ;}
       
       for(j=xmin;j<xmax;j++) 
        {
         zn = &psxZbuf[(i<<10)+j];
         if ((Z > 0) && (!zn->count || zn->z > Z))
          {
           zn->z = Z;
           zn->id = id;
           zn->count++;
          }
         Z += difZ;
         Zf += difZf;
        }
      }
     if(NextRow_Z()) return;
    }
   return;
  }
}

////////////////////////////////////////////////////////////////////////

void drawPoly3Z(int id)
{
 drawPoly3Zi(lx0,ly0,lz0,lx1,ly1,lz1,lx2,ly2,lz2,id);
}
